import base64
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import *


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number','first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser', 'date_joined']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email    = serializers.EmailField(required=False)
    password = serializers.CharField( 
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        username = attrs.get('username')
        email    = attrs.get('email')
        password = attrs.get('password')

        if not email and not username:
            raise serializers.ValidationError(
                'حداقل یکی از فیلدهای username یا email باید پر شود'
            )
        
        if email and username:
            raise serializers.ValidationError(
                'فیلدهای username و email نمیتوانند همزمان پر شوند'
            )
        
        user = None 

        if email:
            user = User.objects.filter(email=email).first()
        if username:
            user = User.objects.filter(username=username).first()
        if user is None:
            raise serializers.ValidationError(
                'کاربری با این مشخصات یافت نشد'
            )
        if not user.check_password(password):
            raise serializers.ValidationError(
                'رمز عبور اشتباه است'
            )
        attrs['user'] = user
        attrs['tokens'] = user.tokens()
        return attrs
    

    def to_representation(self, instance):
        return {
            'user': UserSerializer(instance['user']).data,
            'tokens': instance['tokens']
        }


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    password2 = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'phone_number']
    
    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.pop('password2')
        if password != password2:
            raise serializers.ValidationError(
                'رمز عبور و تکرار آن یکسان نیستند'
            )
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
    def to_representation(self, instance):
        return {
            **UserSerializer(instance).data,
            'tokens': instance.tokens()
        }



class UserInfoSerilizer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField("get_profile_image")

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "birth_date",
            "gender",
            "is_staff",
            "is_active",
            "is_superuser",
            "is_verified",
            "date_joined",
            "profile_image",
        ]
        read_only_fields = [
            "is_staff",
            "is_active",
            "is_superuser",
            "is_verified",
            "date_joined",
            "profile_image",
        ]

    def get_profile_image(self, user):
        return user.profile_image()
    


class UploadBase64ProfileImageSerializer(serializers.ModelSerializer):
    profile_image = serializers.CharField(write_only=True)

    class Meta:
        model = ProfileImage
        fields = ['profile_image']

    def validate_profile_image(self, value):
        if value.startswith("data:image"):
            return value
        raise serializers.ValidationError("فرمت تصویر باید base64 باشد")

    def create(self, validated_data):
        user = validated_data['user']
        profile_image = validated_data['profile_image']
        format, imgstr = profile_image.split(';base64,')
        ext = format.split('/')[-1]
        data = ContentFile(base64.b64decode(imgstr))
        image = InMemoryUploadedFile(data, 'image', f"{user.username}.{ext}", 'image/jpeg', data.__sizeof__, None)
        profile_image = ProfileImage.objects.create(user=user, image=image)
        return profile_image
    

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    new_password2 = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )

    def validate(self, attrs):
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        new_password2 = attrs.get('new_password2')
        if new_password != new_password2:
            raise serializers.ValidationError(
                'The new password and the new password confirmation do not match.'
            )
        print(self.context)
        user = self.context['user']
        if not user.check_password(old_password):
            raise serializers.ValidationError(
                'The old password is incorrect.'
            )
        return attrs
    
    def save(self):
        user = self.context['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    
    
    

class EmailVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=5)
    email = serializers.EmailField()
    
    def validate(self, attrs):
        user = User.objects.get(email=attrs['email'])
        verification = EmailVerification.objects.get(user=user)
        if not user or not verification:
            raise serializers.ValidationError({"email":"ایمیل وارد شده معتبر نیست"})
        if verification.is_expired():
            raise serializers.ValidationError({"code":"کد اعتبار سنجی منقضی شده است"})
        if not verification.is_valid(attrs['code']):
            raise serializers.ValidationError({"code":"کد اعتبار سنجی وارد شده صحیح نیست"})
        return super().validate(attrs)
    
    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data['email'])
        user.is_verified = True
        user.save()
        return user
    
    


class ResendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate(self, attrs):
        user = User.objects.get(email=attrs['email'])
        if not user:
            raise serializers.ValidationError({"email":"ایمیل وارد شده معتبر نیست"})
        if not EmailVerification.objects.filter(user=user).exists():
            raise serializers.ValidationError({"email":"ایمیل وارد شده معتبر نیست"})
        if user.is_verified:
            raise serializers.ValidationError({"email":"ایمیل وارد شده قبلا تایید شده است"})
        return super().validate(attrs)
    
    
class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate(self, attrs):
        user = User.objects.get(email=attrs['email'])
        if not user:
            raise serializers.ValidationError({"email":"ایمیل وارد شده معتبر نیست"})
        return super().validate(attrs)
    
class ForgetPasswordVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=5)
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        user = User.objects.get(email=attrs['email'])
        verification = ForgetPasswordVerification.objects.get(user=user)
        if not user or not verification:
            raise serializers.ValidationError({"email":"ایمیل وارد شده معتبر نیست"})
        if verification.is_expired():
            raise serializers.ValidationError({"code":"کد اعتبار سنجی منقضی شده است"})
        if not verification.is_valid(attrs['code']):
            raise serializers.ValidationError({"code":"کد اعتبار سنجی وارد شده صحیح نیست"})
        return super().validate(attrs)
    
    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user