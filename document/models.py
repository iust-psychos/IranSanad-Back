from django.db import models


class Document(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True)
    content = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_last_seen_by_user(self, user):
        try:
            return DocumentView.objects.filter(document=self, user=user).latest('viewed_at')
        except DocumentView.DoesNotExist:
            return None
        
        
                
class DocumentView(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} viewed {self.document.title} on {self.viewed_at}"



class DocumentUpdate(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='updates')
    update_data = models.BinaryField()  # Stores the Yjs update as binary data
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the update was created

    def __str__(self):
        return f"Update for {self.document.title} at {self.created_at}"