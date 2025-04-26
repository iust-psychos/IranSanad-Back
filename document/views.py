from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action


from .permissions import *
from .serializers import *
from .models import Document


class DocumentViewSet(ModelViewSet):
    """
    A viewset for viewing and editing document instances.
    """

    def get_serializer_class(self):
        if self.action == "document_lookup":
            return DocumentLookupSerializer
        else:
            return DocumentSerializer

    # Suggestion: Uncomment the following line if you want to use a custom lookup field
    # lookup_field = 'doc_uuid'
    serializer_class = DocumentSerializer
    queryset = Document.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=["POST"], detail=False)
    def document_lookup(self, request):
        # TODO:change request type to GET
        serializer = DocumentLookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.validated_data["document"]
        return Response(
            serializer.to_representation(document), status=status.HTTP_200_OK
        )


class DocumentPermissionViewSet(GenericViewSet):
    queryset = AccessLevel.objects.all()

    def get_serializer_class(self):
        if self.action == "set_permission":
            return DocumentSetPermissionSerializer
        elif self.action == "get_permission_list":
            return DocumentGetPermissionsSerializer

    def get_permissions(self):
        if self.action in ["set_permission", "get_permission_list"]:
            return [IsAuthenticated(), IsDocumentAdmin()]
        return super().get_permissions()

    @action(methods=["POST"], detail=False, url_path="set_permission")
    def set_permission(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"changer": request.user}
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        doc = data["document"]

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

    @action(methods=["GET"], detail=False, url_path="get_permission_list/(?P<document>\d+)")
    def get_permission_list(self, request, document=None):
        try:
            document = Document.objects.get(pk=document)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get all access records for this document
        access_levels = AccessLevel.objects.filter(document=document)
        serializer = self.get_serializer(access_levels, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
