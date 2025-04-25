from django.utils.translation import gettext_lazy as _
import base64
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from .models import *

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser', 'date_joined']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        if not email and not username:
            raise serializers.ValidationError(
                _('At least one of the fields "username" or "email" must be filled.')
            )

        if email and username:
            raise serializers.ValidationError(
                _('The fields "username" and "email" cannot be filled simultaneously.')
            )

        user = None

        if email:
            user = User.objects.filter(email=email).first()
        if username:
            user = User.objects.filter(username=username).first()
        if user is None:
            raise serializers.ValidationError(
                _('No user found with the provided credentials.')
            )
        if not user.check_password(password):
            raise serializers.ValidationError(
                _('The password is incorrect.')
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
        write_only=True,
        validators=[validate_password]
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
                _('The password and its confirmation do not match.')
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


class UserInfoSerializer(serializers.ModelSerializer):
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
        raise serializers.ValidationError(_("The image format must be base64."))

    def create(self, validated_data):
        user = validated_data['user']
        profile_image_data = validated_data['profile_image']
        format, imgstr = profile_image_data.split(';base64,')
        ext = format.split('/')[-1]
        data = ContentFile(base64.b64decode(imgstr))
        image = InMemoryUploadedFile(data, 'image', f"{user.username}.{ext}", 'image/jpeg', data.__sizeof__, None)

        # Check if the user already has a profile image
        profile_image, created = ProfileImage.objects.update_or_create(
            user=user,
            defaults={'image': image}
        )
        return profile_image


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True,
        validators=[validate_password]
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
                _('The new password and its confirmation do not match.')
            )
        user = self.context['user']
        if not user.check_password(old_password):
            raise serializers.ValidationError(
                _('The old password is incorrect.')
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
        user = User.objects.filter(email=attrs['email']).first()
        verification = EmailVerification.objects.filter(user=user).first()
        if not user or not verification:
            raise serializers.ValidationError({"email": _("The provided email is invalid.")})
        if verification.is_expired():
            raise serializers.ValidationError({"code": _("The verification code has expired.")})
        if not verification.is_valid(attrs['code']):
            raise serializers.ValidationError({"code": _("The verification code is incorrect.")})
        return super().validate(attrs)

    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data['email'])
        user.is_verified = True
        user.save()
        return user


class ResendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        user = User.objects.filter(email=attrs['email']).first()
        if not user:
            raise serializers.ValidationError({"email": _("The provided email is invalid.")})
        if not EmailVerification.objects.filter(user=user).exists():
            raise serializers.ValidationError({"email": _("The provided email is invalid.")})
        if user.is_verified:
            raise serializers.ValidationError({"email": _("The provided email has already been verified.")})
        return super().validate(attrs)


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        user = User.objects.filter(email=attrs['email']).first()
        if not user:
            raise serializers.ValidationError({"email": _("The provided email is invalid.")})
        return super().validate(attrs)


class ForgetPasswordVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=5)
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        user = User.objects.filter(email=attrs['email']).first()
        verification = ForgetPasswordVerification.objects.filter(user=user).first()
        if not user or not verification:
            raise serializers.ValidationError({"email": _("The provided email is invalid.")})
        if verification.is_expired():
            raise serializers.ValidationError({"code": _("The verification code has expired.")})
        if not verification.is_valid(attrs['code']):
            raise serializers.ValidationError({"code": _("The verification code is incorrect.")})
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password2": _("The new password and its confirmation do not match.")})
        return super().validate(attrs)

    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_password(self.validated_data['new_password'])
        user.save()
        
        return user
class UserLookupSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=False,
        help_text="Enter username (optional if email is provided)")
    email= serializers.EmailField(
        required=True,
        help_text="Enter username (optional if username is provided)")

    user_id = serializers.IntegerField(read_only=True)
    
    def validate(self, attrs):
        if not any([attrs.get('username'), attrs.get('email_address')]):
            raise serializers.ValidationError("باید نام کاربری یا آدرس ایمیل ارائه شود")
        
        
        if attrs.get('username',None):
            user = User.objects.filter(username=attrs.username).first()
        elif attrs.get('email',None):
            user = User.objects.filter(email=attrs.email).first()
        else:
            user = None
            
        if not user:
            raise NotFound("کاربر یافت نشد")
        
        attrs.user = user
        return attrs

    def to_representation(self, instance):
        return {
            'user_id': instance.id,
            'username': instance.username,
            'email_address': instance.email,
        }