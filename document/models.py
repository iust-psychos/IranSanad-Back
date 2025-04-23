from django.db import models


class Document(models.Model):
    title = models.CharField(max_length=255)
    link = models.CharField(max_length=15,unique=True,blank=True)
    owner = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True)
    content = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    