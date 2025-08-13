import logging
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit


logger = logging.getLogger(__name__)

class AuthenticationViewSet(GenericViewSet):
    def get_serializer_class(self):
        if self.action == 'login':
            return LoginSerializer
        elif self.action == 'register':
            return RegisterSerializer
        elif self.action == 'info':
            return UserInfoSerializer
        elif self.action == 'profile':
            return UploadBase64ProfileImageSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action=="user_lookup":
            return UserLookupSerializer
        elif self.action=="signup_email_verification":
            return SignupEmailVerificationSerializer
        elif self.action=="signup_resend_verification":
            return SignupResendVerificationSerializer
        
    def get_permissions(self):
        if self.action in ['login', 'register','signup_email_verification','signup_resend_verification']:
            return []
        else :
            return [IsAuthenticated()]
    

    @method_decorator(ratelimit(key='ip', rate='100/h', method='POST', block=True), name='login')
    @action(detail=False, methods=['POST'])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key='ip', rate='25/h', method='POST', block=True), name='register')
    @action(detail=False, methods=['POST'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods= ['GET', 'PUT', 'PATCH'])
    def info(self, request):
        user = request.user
        if request.method == 'GET':
            return Response(UserInfoSerializer(user).data)
        elif request.method in ['PUT', 'PATCH']:
            serializer = UserInfoSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        

    @action(detail=False, methods=['POST'])
    def profile(self, request):
        user = request.user
        serializer = UploadBase64ProfileImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['POST'])
    def change_password(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(methods=['POST'],detail=False)
    def user_lookup(self,request):
        #TODO:change request type to GET
        serializer = UserLookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(serializer.to_representation(user),status=status.HTTP_200_OK)
    
    @action(methods=['POST'],detail=False)
    def signup_email_verification(self,request):
        serializer = SignupEmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        (verification,created) = SignupEmailVerification.objects.get_or_create(email=serializer.validated_data['email'])
        try:
            verification.send_verification_email()
        except Exception as e:
            logger.error(str(e))
            return Response({"message":"خطا در ارسال ایمیل"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message":"ایمیل تایید ایمیل کاربر ارسال شد"} ,status=status.HTTP_200_OK)
    
    @action(methods=['POST'],detail=False)
    def signup_resend_verification(self,request):
        serializer = SignupResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification = SignupEmailVerification.objects.filter(email=serializer.validated_data['email']).first()
        try:
            verification.send_verification_email()
        except Exception as e:
            logger.error(str(e))
            return Response({"message":"خطا در ارسال ایمیل"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message":"ایمیل تایید ایمیل کاربر ارسال شد"} ,status=status.HTTP_200_OK)
        
    
    @action(methods=['POST'], detail=False)
    def forget_password_verify(self,request):
        serializer = ForgetPasswordVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message":"رمز عبور تغییر یافت"} ,status=status.HTTP_201_CREATED)    
    
    @action(methods=['POST'], detail=False)
    def resend(self,request):
        serializer = ResendEmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.validated_data['email'])
        verification = EmailVerification.objects.get(user=user)
        try:
            verification.send_verification_email()
        except Exception as e:
            logger.error(str(e))
            return Response({"message":"خطا در ارسال ایمیل"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message":"ایمیل تایید مجددا ارسال شد"} ,status=status.HTTP_200_OK)
    
    

class VerificationViewSet(GenericViewSet):
    def get_serializer_class(self):
        if self.action=="verify_email":
            return EmailVerificationSerializer
        elif self.action=="resend":
            return ResendEmailVerificationSerializer
        elif self.action=="forget_password":
            return ForgetPasswordSerializer
        elif self.action=="forget_password_verify":
            return ForgetPasswordVerificationSerializer
        elif self.action=="user_lookup":
            return UserLookupSerializer
        
    @action(methods=['POST'], detail=False)
    def verify_email(self,request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message":"ایمیل تایید شد"} ,status=status.HTTP_200_OK)
    
    
    @action(methods=['POST'], detail=False)
    def resend(self,request):
        serializer = ResendEmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.validated_data['email'])
        verification = EmailVerification.objects.get(user=user)
        try:
            verification.send_verification_email()
        except Exception as e:
            logger.error(str(e))
            return Response({"message":"خطا در ارسال ایمیل"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message":"ایمیل تایید مجددا ارسال شد"} ,status=status.HTTP_200_OK)
    
    
    @action(methods=['POST'], detail=False)
    def forget_password(self,request):
        # TODO: make security better
        serializer = ForgetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.validated_data['email'])
        (verification,created) = ForgetPasswordVerification.objects.get_or_create(user=user)
        try:
            verification.send_verification_email()
        except Exception as e:
            logger.error(str(e))
            return Response({"message":"خطا در ارسال ایمیل"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message":"ایمیل تایید فراموشی رمز عبور ارسال شد"} ,status=status.HTTP_200_OK)
    
    
    @action(methods=['POST'], detail=False)
    def forget_password_verify(self,request):
        serializer = ForgetPasswordVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message":"رمز عبور تغییر یافت"} ,status=status.HTTP_201_CREATED)    