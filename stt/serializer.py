from django.conf import settings
from rest_framework import serializers
from .models import AudioTranscription
import os
from groq import Groq

GROQ_API_KEY = settings.GROQ_API_KEY

class AudioTranscriptionSerializer(serializers.ModelSerializer):
    audio_file = serializers.FileField(write_only=True)
    transcription = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = AudioTranscription
        fields = ['audio_file', 'transcription', 'created_at']
        read_only_fields = ['transcription', 'created_at']

    def create(self, validated_data):
        audio_file = validated_data.get('audio_file')
        user = validated_data.get('user')
        # Step 1: Save instance with audio file only
        instance = AudioTranscription.objects.create(audio_file=audio_file, user=user)
        # Step 2: Get the saved file path
        file_path = instance.audio_file.path
        # Step 3: Transcribe using Groq API
        client = Groq(api_key=GROQ_API_KEY)
        with open(file_path, "rb") as file:
            transcription_result = client.audio.transcriptions.create(
                file=(os.path.basename(file_path), file.read()),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
            )
        transcription_text = transcription_result.text
        # Step 4: Update instance with transcription
        instance.transcription = transcription_text
        instance.save(update_fields=["transcription"])
        return instance


