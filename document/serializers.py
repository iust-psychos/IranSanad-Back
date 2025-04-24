import logging
from rest_framework import serializers
from .models import *
from .utility import link_generator

logger = logging.getLogger(__name__)

class DocumentSerializer(serializers.ModelSerializer):    
    owner_name = serializers.SerializerMethodField(method_name='get_owner_name')
    last_seen = serializers.SerializerMethodField(method_name='get_last_seen')
    
    def get_owner_name(self, obj):
        request_user = self.context.get('request').user
        if request_user and request_user.id == obj.owner.id:
            return 'Me'
        return obj.owner.username if obj.owner else 'Unknown'
    
    def get_last_seen(self, obj):
        request_user = self.context.get('request').user
        last_seen = DocumentView.objects.filter(document=obj, user=request_user).order_by('-viewed_at').first()
        return last_seen.viewed_at if last_seen else None

    class Meta:
        model = Document
        fields = ['id', 'doc_uuid', 'title', 'owner', 'owner_name', 'created_at', 'updated_at', 'link', 'is_public', 'last_seen']
        read_only_fields = ['id', 'doc_uuid', 'owner', 'created_at', 'updated_at', 'link', 'last_seen', 'is_public']

    def create(self, validated_data):
        document = Document.objects.create(**validated_data)
        generated_link = link_generator(f"{document.title}{document.created_at.timestamp()}")

        document.link = generated_link
        document.save()
        
        logger.info(f"Document created with link: {generated_link}")
        
        return document