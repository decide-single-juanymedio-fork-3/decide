from rest_framework import serializers
from .models import CensusGroup

class CensusGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CensusGroup
        fields = '__all__' 
