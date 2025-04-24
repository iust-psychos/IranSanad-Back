from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import *
from .models import Document


class DocumentViewSet(ModelViewSet):
    """
    A viewset for viewing and editing document instances.
    """
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
    
    
