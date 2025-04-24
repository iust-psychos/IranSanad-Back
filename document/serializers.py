from rest_framework import serializers
from .models import *
from .utility import link_generator

class DocumentSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Document
        fields = ['id', 'title', 'owner', 'created_at', 'updated_at', 'link']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'link']

    def create(self, validated_data):
        print('create called')
        # Create the document first
        document = Document.objects.create(**validated_data)
        print('after creation caled')
        # Generate and set the link
        generated_link = link_generator(f"{document.title}{document.created_at.timestamp()}")
        print(f'*********************{generated_link}*************************')
        document.link = generated_link
        document.save()
        
        return document