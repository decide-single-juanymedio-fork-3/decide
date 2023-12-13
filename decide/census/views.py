from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED as ST_201,
        HTTP_204_NO_CONTENT as ST_204,
        HTTP_400_BAD_REQUEST as ST_400,
        HTTP_401_UNAUTHORIZED as ST_401,
        HTTP_409_CONFLICT as ST_409
)

from base.perms import UserIsStaff
from .models import Census, CensusGroup
from .serializers import CensusGroupSerializer

from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib import messages
import io
import csv



class CensusCreate(generics.ListCreateAPIView):
    permission_classes = (UserIsStaff,)

    def create(self, request, *args, **kwargs):
        voting_id = request.data.get('voting_id')
        voters = request.data.get('voters')
        try:
            for voter in voters:
                census = Census(voting_id=voting_id, voter_id=voter)
                census.save()
        except IntegrityError:
            return Response('Error try to create census', status=ST_409)
        return Response('Census created', status=ST_201)

    def list(self, request, *args, **kwargs):
        voting_id = request.GET.get('voting_id')
        voters = Census.objects.filter(voting_id=voting_id).values_list('voter_id', flat=True)
        return Response({'voters': voters})


class CensusDetail(generics.RetrieveDestroyAPIView):

    def destroy(self, request, voting_id, *args, **kwargs):
        voters = request.data.get('voters')
        census = Census.objects.filter(voting_id=voting_id, voter_id__in=voters)
        census.delete()
        return Response('Voters deleted from census', status=ST_204)

    def retrieve(self, request, voting_id, *args, **kwargs):
        voter = request.GET.get('voter_id')
        try:
            Census.objects.get(voting_id=voting_id, voter_id=voter)
        except ObjectDoesNotExist:
            return Response('Invalid voter', status=ST_401)
        return Response('Valid voter')


class CensusGroupCreate(generics.CreateAPIView):
    permission_classes = (UserIsStaff,)
    serializer_class = CensusGroupSerializer

class CensusGroupList(generics.ListAPIView):
    permission_classes = (UserIsStaff,)
    serializer_class = CensusGroupSerializer
    queryset = CensusGroup.objects.all()

class CensusGroupDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (UserIsStaff,)
    serializer_class = CensusGroupSerializer
    queryset = CensusGroup.objects.all()

def import_census_csv(request):
    if request.method == 'POST' and request.FILES['csv_import_file']:
        csv_file = request.FILES['csv_import_file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'El archivo seleccionado no es un archivo CSV válido.')
            return render(request, 'census/upload.html', status=400)

        else:
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            reader = csv.reader(io_string)
            rows = 0
            for row in reader:
                if len(row) >= 2:
                    username = row[0].strip()
                    voting_id = row[1].strip()
                    voter = User.objects.get(username=username)
                    existing_census = Census.objects.filter(voter_id=voter.id, voting_id=voting_id)
                    if not existing_census.exists():
                        Census.objects.create(voting_id=voting_id, voter_id=voter.id)
                    rows += 1
            messages.success(request, 'Se han añadido ' + str(rows) + ' usuarios al censo.')          
    return render(request, 'census/upload.html', status=201)