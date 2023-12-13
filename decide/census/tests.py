from django.contrib.auth.models import User
from django.http import Http404
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.by import By

from .models import Census, CensusGroup
from base.tests import BaseTestCase
from datetime import datetime

from django.conf import settings
import os


class CensusTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.census = Census(voting_id=1, voter_id=1)
        self.census.save()

    def tearDown(self):
        super().tearDown()
        self.census = None

    def test_check_vote_permissions(self):
        response = self.client.get('/census/{}/?voter_id={}'.format(1, 2), format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), 'Invalid voter')

        response = self.client.get('/census/{}/?voter_id={}'.format(1, 1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Valid voter')

    def test_list_voting(self):
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'voters': [1]})

    def test_add_new_voters_conflict(self):
        data = {'voting_id': 1, 'voters': [1]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 409)

    def test_add_new_voters(self):
        data = {'voting_id': 2, 'voters': [1,2,3,4]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(data.get('voters')), Census.objects.count() - 1)

    def test_destroy_voter(self):
        data = {'voters': [1]}
        response = self.client.delete('/census/{}/'.format(1), data, format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, Census.objects.count())


class CensusGroupTests(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        self.censusGroup = CensusGroup(groupName = 'Group')
        self.censusGroup.save()

    def tearDown(self):
        super().tearDown()
        self.censusGroup = None

    def test_add_users_to_group(self):
        self.censusGroup.voters.add(self.user1, self.user2)
        self.censusGroup.save()
        self.assertEqual(self.censusGroup.voters.count(), 2)


    def test_list_permissions(self):
        response = self.client.get('/census/censusgroup/list/', format='json')
        self.assertEqual(response.status_code, 401)
        self.login(user='noadmin')
        response = self.client.get('/census/censusgroup/list/', format='json')
        self.assertEqual(response.status_code, 403)
        self.login(user='admin')
        response = self.client.get('/census/censusgroup/list/', format='json')
        self.assertEqual(response.status_code, 200)

    def test_detail_permissions(self):
        response = self.client.get('/census/censusgroup/detail/{}/'.format(self.censusGroup.id), format='json')
        self.assertEqual(response.status_code, 401)
        self.login(user='noadmin')
        response = self.client.get('/census/censusgroup/detail/{}/'.format(self.censusGroup.id), format='json')
        self.assertEqual(response.status_code, 403)
        self.login(user='admin')
        response = self.client.get('/census/censusgroup/detail/{}/'.format(self.censusGroup.id), format='json')
        self.assertEqual(response.status_code, 200)
    
    def test_create_permissions(self):
        data = {
            "groupName": "Test Census Group",
            "voters": [self.user1.id, self.user2.id]  
        }
        response = self.client.post('/census/censusgroup/create/', data, format='json')
        self.assertEqual(response.status_code, 401)
        self.login(user='noadmin')
        response = self.client.post('/census/censusgroup/create/', data, format='json')
        self.assertEqual(response.status_code, 403)
        self.login(user='admin')
        response = self.client.post('/census/censusgroup/create/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_create_group(self):
        data = {
            "groupName": "Test Census Group",
            "voters": [self.user1.id, self.user2.id]  
        }
        self.login(user='admin')
        response = self.client.post('/census/censusgroup/create/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(CensusGroup.objects.count(), 2)
    
    def test_apply_census(self):
        self.censusGroup.voters.add(self.user1, self.user2)
        self.censusGroup.voting_id = 1
        self.censusGroup.save()
        self.censusGroup.applyCensus()
        censuses_count = Census.objects.filter(voting_id=1).count()
        self.assertEqual(censuses_count, 2)

class TestUploadCSV(BaseTestCase):
    def setUp(self):
        super().setUp()

        # Se definen usuarios para el censo
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2') 

    def tearDown(self):
        super().tearDown()
        self.user1 = None
        self.user2 = None

    def test_upload_invalid_csv_file(self):
        ruta = os.path.join(settings.BASE_DIR, 'census', 'csv_test_files', 'invalid_file.txt')
        with open(ruta, 'rb') as file:
            try:
                response = self.client.post('/census/import/', {'csv_import_file': file})
            except Http404:
                pass
        self.assertEqual(response.status_code, 400)  # Verifica que la vista responda Bad request (código 400)
    
    def test_upload_valid_csv_file(self):
        ruta = os.path.join(settings.BASE_DIR, 'census', 'csv_test_files', 'valid_file.csv')
        with open(ruta, 'rb') as file:
            try:
                response = self.client.post('/census/import/', {'csv_import_file': file})
            except Http404:
                pass
        self.assertEqual(response.status_code, 201)  # Verifica que la vista responda Objeto creado (código 201)
        self.assertEqual(Census.objects.count(), 2)  # Verifica que existen dos censos creados

class CensusTest(StaticLiveServerTestCase):
    def setUp(self):
        #Load base test functionality for decide
        self.base = BaseTestCase()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

        self.base.tearDown()
    
    def createCensusSuccess(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/census/census/add")
        now = datetime.now()
        self.cleaner.find_element(By.ID, "id_voting_id").click()
        self.cleaner.find_element(By.ID, "id_voting_id").send_keys(now.strftime("%m%d%M%S"))
        self.cleaner.find_element(By.ID, "id_voter_id").click()
        self.cleaner.find_element(By.ID, "id_voter_id").send_keys(now.strftime("%m%d%M%S"))
        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/census/census")

    def createCensusEmptyError(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/census/census/add")

        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[3]/div/div[1]/div/form/div/p').text == 'Please correct the errors below.')
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/census/census/add")

    def createCensusValueError(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/census/census/add")
        now = datetime.now()
        self.cleaner.find_element(By.ID, "id_voting_id").click()
        self.cleaner.find_element(By.ID, "id_voting_id").send_keys('64654654654654')
        self.cleaner.find_element(By.ID, "id_voter_id").click()
        self.cleaner.find_element(By.ID, "id_voter_id").send_keys('64654654654654')
        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[3]/div/div[1]/div/form/div/p').text == 'Please correct the errors below.')
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/census/census/add")

