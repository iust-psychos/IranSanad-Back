from rest_framework import serializers
from .models import *


class DocumentSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Document
        fields = ['id', 'title', 'owner', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']