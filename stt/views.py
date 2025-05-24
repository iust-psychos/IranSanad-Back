from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from .serializer import AudioTranscriptionSerializer
from .models import AudioTranscription
from rest_framework.parsers import MultiPartParser


class AudioTranscriptionViewSet(CreateModelMixin, GenericViewSet):
    """
    A viewset for creating audio transcriptions.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, )

    def get_queryset(self):
        return AudioTranscription.objects.all()
    
    def get_serializer_class(self):
        return AudioTranscriptionSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)