from django.db import models


class AudioTranscription(models.Model):
    user = models.ForeignKey(
        'authentication.User', on_delete=models.SET_NULL, related_name='transcriptions', null=True, blank=True
    )
    audio_file = models.FileField(upload_to='audio_files/')
    transcription = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transcription {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    