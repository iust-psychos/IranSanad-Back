from django.db import models


class Document(models.Model):
    ACCESS_LEVELS = {
        4 : 'Owner',
        3 : 'Admin',
        2 : 'Writer',
        1 : 'Read_Only',
        0 : 'Deny',
    }
    title = models.CharField(max_length=255)
    link = models.CharField(max_length=15,unique=True,blank=True)
    owner = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True)
    content = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    default_access_level = models.PositiveSmallIntegerField(choices=ACCESS_LEVELS,default=2)
    
    def __str__(self):
        return self.title
    
class AccessLevel(models.Model):
    ACCESS_LEVELS = {
        4 : 'Owner',
        3 : 'Admin',
        2 : 'Writer',
        1 : 'Read_Only',
        0 : 'Deny',
    }
    
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    document = models.ForeignKey(Document , on_delete=models.CASCADE)
    access_level = models.PositiveSmallIntegerField(choices=ACCESS_LEVELS,default=2)
    
    class Meta:
        unique_together = ('user', 'document')
        
    def __str__(self):
        return f'{self.user} has {self.ACCESS_LEVELS[self.access_level]} access to {self.document}'
    