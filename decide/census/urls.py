from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('censusgroup/create/', views.CensusGroupCreate.as_view(), name='censusgroup_create'),
    path('censusgroup/list/', views.CensusGroupList.as_view(), name='censusgroup_list'),
    path('censusgroup/detail/<int:pk>/', views.CensusGroupDetail.as_view(), name='censusgroup_detail'),
]
