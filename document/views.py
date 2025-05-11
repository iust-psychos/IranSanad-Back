from django.db.models import Q
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.conf import settings

from .utility import *
from .permissions import *
from .serializers import *
from .models import *

SENDER_EMAIL = settings.EMAIL_HOST_USER


class DocumentViewSet(ModelViewSet):
    """
    A viewset for viewing and editing document instances.
    """

    def get_serializer_class(self):
        if self.action == "document_lookup":
            return DocumentLookupSerializer
        elif self.action == "suggest_next_word":
            return SuggestNextWordSerializer
        else:
            return DocumentSerializer

    # Suggestion: Uncomment the following line if you want to use a custom lookup field
    lookup_field = "doc_uuid"
    serializer_class = DocumentSerializer
    queryset = Document.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == "list":
            documents = (
                AccessLevel.objects.filter(user_id=self.request.user.id)
                .filter(access_level__gte=1)
                .values_list("document_id", flat=True)
            )
            queryset = self.queryset.filter(
                Q(id__in=documents) | Q(owner=self.request.user)
            )
            return queryset
        else:
            return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        document = serializer.save(owner=self.request.user)
        AccessLevel.objects.create(
            user=self.request.user,
            document=document,
            access_level=AccessLevel.PERMISSION_MAP["Owner"],
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=["POST"], detail=False)
    def document_lookup(self, request):
        # TODO:change request type to GET
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.validated_data["document"]
        return Response(
            serializer.to_representation(document), status=status.HTTP_200_OK
        )
        
    @action(methods=["POST"], detail=False)
    def suggest_next_word(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        suggestions =suggest_next_words(serializer.validated_data['text'])
        return Response(
            serializer.to_representation(suggestions) ,status=status.HTTP_200_OK
        )
        
        
        

class DocumentPermissionViewSet(GenericViewSet):
    queryset = AccessLevel.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "set_permission":
            return DocumentSetPermissionSerializer
        elif self.action == "get_permission_list":
            return DocumentGetPermissionsSerializer
        elif self.action == "get_user_permission":
            return GetUserPermissionsSerializer

    @action(methods=["POST"], detail=False)
    def set_permission(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"changer": request.user}
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        doc = data["document"]
        send_email = data["send_email"]

        # Update permissions
        results = []
        for permission in data["permissions"]:
            user = permission["user"]
            perm_level = UserPermissionSerializer.PERMISSION_MAP[
                permission["permission"]
            ]
            AccessLevel.objects
            AccessLevel.objects.update_or_create(
                user=user, document=doc, defaults={"access_level": perm_level}
            )
            if send_email:
                default_message = (
                    f"{user.username} شما را به مشارکت در سند {doc.title} دعوت کرده"
                )
                message = (
                    data.get("email_message",None) if data.get("email_message",None) else default_message
                )
                document_url = f"{settings.FRONTEND_BASE_URL}/{add_dash(doc.link)}"
                message += f"\n\nلینک ورود به سند: {document_url}"
                try:
                    user.email_user(
                        f"دعوت به مشارکت در سند '{doc.title}'", message, SENDER_EMAIL
                    )
                except:
                    return Response(
                        {
                            "document": doc.id,
                            "results": results,
                            "message": "متاسفانه در هنگام ارسال ایمیل مشکلی پیش آمده",
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            results.append(
                {
                    "user": user.id,
                    "permission": permission["permission"],
                    "status": "success",
                }
            )

        return Response(
            {"document": doc.id, "results": results}, status=status.HTTP_200_OK
        )

    @action(
        methods=["GET"], detail=False, url_path="get_permission_list/(?P<document>\d+)"
    )
    def get_permission_list(self, request, document=None):
        # document = request.query_params.get('document')
        try:
            document = Document.objects.get(pk=document)
        except Document.DoesNotExist:
            return Response(
                {"message": "Document not found"}, status=status.HTTP_404_NOT_FOUND
            )
        # making sure share access is public or user is owner or admin
        if not (
            document.public_premission_access
            or (
                request.user == document.owner
                or AccessLevel.objects.filter(
                    user=request.user,
                    document=document,
                    access_level__gte=AccessLevel.PERMISSION_MAP["Admin"],
                ).exists()
            )
        ):
            return Response(
                {
                    "message": "You don't have permission to get permissions for this document"
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        # Get all access records for this document
        access_levels = AccessLevel.objects.filter(document=document).order_by(
            "-access_level"
        )
        serializer = self.get_serializer(
            access_levels, many=True, context={"user": request.user}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"], detail=False, url_path="get_user_permission/(?P<document>\d+)"
    )
    def get_user_permission(self, request, document=None):
        try:
            document = Document.objects.get(pk=document)
        except Document.DoesNotExist:
            return Response(
                {"message": "Document not found"}, status=status.HTTP_404_NOT_FOUND
            )
        access_instance = AccessLevel.objects.filter(
            document=document, user=request.user
        ).first()
        access_level = (
            access_instance.access_level
            if access_instance
            else document.default_access_level
        )
        data = {
            "access_level": AccessLevel.ACCESS_LEVELS[access_level],
            "can_write": access_level > 1,
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    

class CommentViewSet(ModelViewSet):

    serializer_class = CommentSerializer

    def get_queryset(self):
        doc_id = self.kwargs["doc_id"]
        is_resolved = self.request.query_params.get("is_resolved", None)
        queryset = (
            Comment.objects.filter(document=doc_id)
            .select_related("author", "resolved_by")
            .prefetch_related("commentreply_set")
        )
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == "true")
        return queryset
    