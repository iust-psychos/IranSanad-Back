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

    serializer_class = DocumentSerializer
    queryset = Document.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentPermissionViewSet(GenericViewSet):
    serializer_class = DocumentPermissionSerializer
    queryset = AccessLevel.objects.all()

    def get_permissions(self):
        if self.action == "set_permission":
            return [IsAuthenticated(),IsDocumentAdmin()]
        return super().get_permissions()

    @action(methods=["POST"], detail=False, url_path='permission')
    def set_permission(self, request):
        serializer = self.get_serializer(data=request.data, context={'changer': request.user})
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        doc = data["document"]
        
        # Update permissions
        results = []
        for permission in data["permissions"]:
            user = permission['user']
            perm_level = UserPermissionSerializer.PERMISSION_MAP[permission['permission']]
            
            AccessLevel.objects.update_or_create(
                user=user,
                document=doc,
                access_level = perm_level
            )
            results.append({
                'user': user.id,
                'permission': permission['permission'],
                'status': 'success'
            })
        
        return Response({
            'document': doc.id,
            'results': results
        }, status=status.HTTP_200_OK)
