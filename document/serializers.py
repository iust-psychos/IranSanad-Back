import logging
from rest_framework import serializers
from .models import *
from .utility import *
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, PermissionDenied

User = get_user_model()
logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField("get_profile_image")

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile_image"]
        read_only_fields = ["id", "username", "email", "profile_image"]

    def get_profile_image(self, user):
        return user.profile_image()


class DocumentSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField(method_name="get_owner_name")
    last_seen = serializers.SerializerMethodField(method_name="get_last_seen")

    def get_owner_name(self, obj):
        request_user = self.context.get("request").user
        if request_user and request_user.id == obj.owner.id:
            return "Me"
        return obj.owner.username if obj.owner else "Unknown"

    def get_last_seen(self, obj):
        request_user = self.context.get("request").user
        last_seen = (
            DocumentView.objects.filter(document=obj, user=request_user)
            .order_by("-viewed_at")
            .first()
        )
        return last_seen.viewed_at if last_seen else None

    class Meta:
        model = Document
        fields = [
            "id",
            "doc_uuid",
            "title",
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
            "link",
            "is_public",
            "last_seen",
        ]
        read_only_fields = [
            "id",
            "doc_uuid",
            "owner",
            "created_at",
            "updated_at",
            "link",
            "last_seen",
            "is_public",
        ]

    def create(self, validated_data):
        document = Document.objects.create(**validated_data)
        generated_link = link_generator(
            f"{document.title}{document.created_at.timestamp()}"
        )

        document.link = generated_link
        document.save()

        return document


class UserPermissionSerializer(serializers.Serializer):
    PERMISSION_MAP = AccessLevel.PERMISSION_MAP

    user = serializers.IntegerField()
    permission = serializers.ChoiceField(choices=list(PERMISSION_MAP.keys()))

    def validate_user(self, value):
        try:
            return User.objects.get(pk=value)
        except User.DoesNotExist:
            raise NotFound(f"User {value} does not exist")


class DocumentSetPermissionSerializer(serializers.Serializer):
    document = serializers.IntegerField()
    permissions = serializers.ListField(child=UserPermissionSerializer(), min_length=1)
    send_email = serializers.BooleanField(write_only=True, default=False)
    email_message = serializers.CharField(write_only=True, required=False)

    def validate_document(self, value):
        try:
            return Document.objects.get(pk=value)
        except Document.DoesNotExist:
            raise NotFound(f"Document with id = '{value}' does not exist")

    def validate(self, attrs):
        doc = attrs["document"]
        changer = self.context["changer"]

        # Verify changer has permission to modify this document
        if not (
            doc.public_premission_access
            or (
                changer == doc.owner
                or AccessLevel.objects.filter(
                    user=changer,
                    document=doc,
                    access_level__gte=AccessLevel.PERMISSION_MAP["Admin"],
                ).exists()
            )
        ):
            raise PermissionDenied(
                "You don't have permission to modify permissions for this document"
            )

        for permission in attrs["permissions"]:
            user = permission.get("user")
            perm_level = UserPermissionSerializer.PERMISSION_MAP[
                permission["permission"]
            ]

            # Prevent changing owner permissions
            if user == doc.owner and perm_level != AccessLevel.PERMISSION_MAP["Owner"]:
                raise PermissionDenied("Cannot change owner's permissions")
            elif (
                user == doc.owner and perm_level == AccessLevel.PERMISSION_MAP["Owner"]
            ):
                attrs.pop(permission)
                continue
            # Prevent setting permissions higher than your own
            changer_level = (
                UserPermissionSerializer.PERMISSION_MAP["Owner"]
                if changer == doc.owner
                else AccessLevel.objects.get(user=changer, document=doc).access_level
            )
            if perm_level > changer_level:
                raise PermissionDenied(
                    f"Cannot set permission level higher than your own (permission level {changer_level} , requested change level{perm_level})"
                )

        return attrs


class DocumentGetPermissionsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    access_level = serializers.SerializerMethodField("get_access_level")

    class Meta:
        model = AccessLevel
        fields = ["user", "access_level"]

    def get_access_level(self, access_instance):
        return AccessLevel.ACCESS_LEVELS[access_instance.access_level]


class GetUserPermissionsSerializer(serializers.Serializer):
    access_level = serializers.CharField()
    can_write = serializers.BooleanField()


class DocumentLookupSerializer(serializers.Serializer):
    link = serializers.CharField(required=False)
    doc_uuid = serializers.UUIDField(required=False)
    title = serializers.CharField(read_only=True)
    document_id = serializers.IntegerField(read_only=True)

    def validate(self, attrs):
        if not any([attrs.get("link"), attrs.get("doc_uuid")]):
            raise serializers.ValidationError(
                "link or doc_uuid must be filled(one of them is enough)"
            )

        if attrs.get("link", None):
            document = Document.objects.filter(link=remove_dash(attrs["link"])).first()
        elif attrs.get("doc_uuid", None):
            document = Document.objects.filter(doc_uuid=attrs["doc_uuid"]).first()
        else:
            document = None
        if not document:
            raise NotFound("سند یافت نشد")

        attrs["document"] = document
        return attrs

    def to_representation(self, instance):
        return {
            "document_id": instance.id,
            "title": instance.title,
            "link": instance.link,
            "doc_uuid": instance.doc_uuid,
        }


class CommentReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentReply
        fields = [
            "id",
            "author",
            "text",
            "created_at",
            "updated_at",
        ]

    author = UserSerializer(read_only=True)


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            "document_uuid",
            "author",
            "author_username",
            "text",
            "range_start",
            "range_end",
            "is_resolved",
            "resolved_by",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]

    author = serializers.CharField(source="author.username", write_only=True)
    author_username = serializers.SerializerMethodField(read_only=True)
    document_uuid = serializers.UUIDField(source="document.doc_uuid", write_only=True)

    def get_author_username(self, obj):
        return obj.author.username

    def validate_author(self, value):
        try:
            author = User.objects.get(username=value)
            return author
        except User.DoesNotExist:
            raise serializers.ValidationError(
                f"Author with username '{value}' does not exist."
            )

    def validate_document(self, value):
        try:
            document = Document.objects.get(doc_uuid=value)
            return document
        except Document.DoesNotExist:
            raise serializers.ValidationError(
                f"Document with uuid '{value}' does not exist."
            )

    def create(self, validated_data):
        author_username = validated_data.pop("author")["username"]
        documet_uuid = validated_data.pop("document")["doc_uuid"]
        author = self.validate_author(author_username)
        document = self.validate_document(documet_uuid)
        validated_data["author"] = author
        validated_data["document"] = document
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "author" in validated_data:
            author_username = validated_data.pop("author")["username"]
            author = self.validate_author(author_username)
            validated_data["author"] = author
        return super().update(instance, validated_data)
