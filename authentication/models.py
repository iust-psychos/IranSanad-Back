from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from rest_framework_simplejwt.tokens import RefreshToken


class User(AbstractUser):

    phone_number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{12,15}$',
                message="شماره تلفن باید به شکل +989123456789 وارد شود"
            ),
        ],
        blank=True,
        null=True,
        unique=True
    )
    email = models.EmailField(unique=True)

    GENDER_CHOICES = (("M", "Male"), ("F", "Female"), ("O", "Other"))

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)

    birth_date = models.DateField(blank=True, null=True)



    def __str__(self):
        return self.username

    def tokens(user):
        refresh = RefreshToken.for_user(user)
        return {
            "access":str(refresh.access_token),
            "refresh":str(refresh)
        }
    

    def profile_image(self):
        return self.profileimage.image.url if hasattr(self, "profileimage") else None



class ProfileImage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="profile_images", blank=True, null=True)

    def __str__(self):
        return self.user.username

#must be removed from here and be added to core later
class Document(models.Model):
    document_name=models.CharField(max_length=30)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_created=models.DateTimeField(auto_now_add=True,blank=True,editable=False)
    last_modified = models.DateTimeField(auto_now=True,blank=True)
    last_visited= models.DateTimeField(auto_now=True,blank=True)
    
    def __str__(self):
        return self.document_name

    