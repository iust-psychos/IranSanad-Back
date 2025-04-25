import logging
from rest_framework import serializers
from .models import *
from .utility import link_generator
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, PermissionDenied

User = get_user_model()
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
      
class UserPermissionSerializer(serializers.Serializer):
    PERMISSION_MAP = {"Owner": 4, "Admin": 3, "Write": 2, "ReadOnly": 1, "Deny": 0}

    user = serializers.IntegerField()
    permission = serializers.ChoiceField(choices=list(PERMISSION_MAP.keys()))

    def validate_user(self, value):
        try:
            return User.objects.get(pk=value)
        except User.DoesNotExist:
            raise NotFound(f"User {value} does not exist")


class DocumentPermissionSerializer(serializers.Serializer):
    document = serializers.IntegerField()
    permissions = serializers.ListField(child=UserPermissionSerializer(), min_length=1)

    def validate_document(self, value):
        try:
            return Document.objects.get(pk=value)
        except Document.DoesNotExist:
            raise NotFound(f"Document {value} does not exist")

    def validate(self, attrs):
        doc = attrs["document"]
        changer = self.context["changer"]

        # Verify changer has permission to modify this document
        if not (
            changer == doc.owner
            or AccessLevel.objects.filter(
                user=changer,
                document=doc,
                access_level__gte=self.PERMISSION_MAP["Admin"],
            ).exists()
        ):
            raise PermissionDenied(
                "You don't have permission to modify permissions for this document"
            )

        for permission in attrs["permissions"]:
            user = permission.get('user')
            perm_level = UserPermissionSerializer.PERMISSION_MAP[permission['permission']]

            # Prevent changing owner's permissions unless you're the owner
            if user == doc.owner and changer != doc.owner:
                raise PermissionDenied("Cannot change owner's permissions")

            # Prevent setting permissions higher than your own
            changer_level = (
                UserPermissionSerializer.PERMISSION_MAP["Owner"]
                if changer == doc.owner
                else AccessLevel.objects.get(user=changer, document=doc).access_level
            )
            if perm_level > changer_level:
                raise PermissionDenied(
                    f"Cannot set permission level higher than your own (permission level {changer_level} and {perm_level})"
                )

        return attrs
