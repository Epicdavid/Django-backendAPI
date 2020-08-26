from allauth.account import app_settings as allauth_settings
from allauth.account.models import EmailAddress
from allauth.utils import (email_address_exists,
                            get_username_max_length)
from allauth.account.utils import setup_user_email
from rest_framework import status
from rest_framework.exceptions import APIException
from django.utils.encoding import force_text
from rest_framework.views import exception_handler
import re

from rest_framework import serializers,exceptions
from rest_auth.registration.serializers import RegisterSerializer
from rest_auth.serializers import LoginSerializer
from .models import *
from allauth.account.adapter import get_adapter
from rest_framework.authtoken.models import Token
from pinax.referrals.models import Referral
from datetime import datetime
from allauth.account.views import SignupView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model, authenticate

from django.contrib.auth.validators import ASCIIUsernameValidator



class Contact(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    company = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    subject = serializers.CharField()
    message = serializers.CharField()


class Login(LoginSerializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def authenticate(self, **kwargs):
        return authenticate(self.context['request'], **kwargs)

    def _validate_email(self, email, password):
        user = None

        if email and password:
            user = self.authenticate(email=email, password=password)
        else:
            msg = _('Must include "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username(self, username, password):
        user = None

        if username and password:
            user = self.authenticate(username=username, password=password)
        else:
            msg = _('Must include "username" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username_email(self, username, email, password):
        user = None

        if email and password:
            user = self.authenticate(email=email, password=password)
        elif username and password:
            user = self.authenticate(username=username, password=password)
        else:
            msg = _('Must include either "username" or "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        user = None

        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account import app_settings

            # Authentication through email
            if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.EMAIL:
                user = self._validate_email(email, password)

            # Authentication through username
            elif app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.USERNAME:
                user = self._validate_username(username, password)

            # Authentication through either username or email
            else:
                user = self._validate_username_email(username, email, password)

        else:
            # Authentication without using allauth
            if email:
                try:
                    username = UserModel.objects.get(email__iexact=email).get_username()
                except UserModel.DoesNotExist:
                    pass

            if username:
                user = self._validate_username_email(username, '', password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise CustomValidation(
                    'User account is disabled.',"error",status_code=status.HTTP_200_OK)

        else:
            msg = _('Unable to log in with provided credentials.')
            raise CustomValidation(
                   'Unable to log in with provided credentials.',"error",status_code=status.HTTP_200_OK)


        # If required, is the email verified?
        if 'rest_auth.registration' in settings.INSTALLED_APPS:
            from allauth.account import app_settings
            if app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise CustomValidation('E-mail is not verified.',"error",status_code=status.HTTP_200_OK)

        attrs['user'] = user
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """
    email = serializers.EmailField()

    password_reset_form_class = PasswordResetForm

    def get_email_options(self):
        """Override this method to change default e-mail options"""
        return {}


    def validate_email(self, value):
        # Create PasswordResetForm with the serializer
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors)
        if not get_user_model().objects.filter(email=value).exists():
            raise CustomValidation('Account not found',"error",status_code=status.HTTP_200_OK)
        return value

    def save(self):
        request = self.context.get('request')
        # Set some values to trigger the send_email method.
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': request,
        }

        opts.update(self.get_email_options())
        self.reset_form.save(**opts)

class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'        

class CustomValidation(APIException):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        default_detail = 'A server error occurred.'

        def __init__(self, detail, field, status_code):
            if status_code is not None:self.status_code = status_code
            if detail is not None:
                self.detail = {field: force_text(detail)}
            else: self.detail = {'error': force_text(self.default_detail)}



class UpdateUserSerializer(serializers.ModelSerializer):

    is_verified = serializers.SerializerMethodField()

    def get_is_verified(self, user):    
        return (user.emailaddress_set.filter().exists())

    class Meta:
        model = User
        fields = ('email','btc_wallet','first_name','last_name','address','city','country','zip_code','is_verified') 

    def update(self, instance, validated_data):
        new_email = validated_data.pop('email', None)
        user = super(UpdateUserSerializer, self).update(instance, validated_data)

       
        if new_email:
            context = self.context
            request = context.get('request', None)
            if request:
                EmailAddress.objects.add_email(request, user, new_email, confirm=True)

        return user

class SignupSerializer(RegisterSerializer):
    btc_wallet = serializers.CharField(max_length=300) 
    class Meta:
        model = User
        fields = ('email','username','password','btc_wallet','user') 


    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
            'btc_wallet': self.validated_data.get('btc_wallet', ''),
            'email': self.validated_data.get('email', '')
        }


    def validate_username(self, value):
        existing = User.objects.filter(username__iexact=value)
        if existing.exists():
            raise CustomValidation(
                    "A user is already registered with this name.","error",status_code=status.HTTP_200_OK)
        if not re.match(r'^[\w.@+-]+\Z', value):
            raise CustomValidation(
                    "username may contain only letters, numbers.","error",status_code=status.HTTP_200_OK)
 
        else:
            return value    

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise CustomValidation(
                    "A user is already registered with this e-mail address.","error",status_code=status.HTTP_200_OK)
        return email

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        user.is_student = True  
        adapter.save_user(request, user, self)
        return user



class TokenSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()
   
    
    class Meta:
        model= Token 
        fields = ('key','user','user_detail')

    def get_user_detail(self, obj):
        serializer_data = UserSerializer(obj.user).data
        usern =  serializer_data.get('username')
        user = User.objects.get(username=usern)
        ref = user.profile.referral.url
        if user.profile.referredBy is not None:
            reff = user.profile.referredBy
            referral = reff.username
        else:
            referral = ""
        is_student = serializer_data.get('is_student')
        is_staff = serializer_data.get('is_staff')
        username = serializer_data.get('username')
        email = serializer_data.get('email')
        email_verified = serializer_data.get('email_verified')
        btc_wallet = serializer_data.get('btc_wallet')
        compounding = serializer_data.get('compounding')
        withdrawn = serializer_data.get('totalWithdrawn')
        time = serializer_data.get('date_joined')
        date = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%B')
        urlhash = serializer_data.get('urlhash')
        balance = serializer_data.get('account_balance')
        last = serializer_data.get('last_login')
        last_login = datetime.strptime(last, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%I:%M%p on %d %B %Y')
        activeA = serializer_data.get('active_affiliates')
        activeP = serializer_data.get('active_package')
        first_name = serializer_data.get('first_name')
        last_name = serializer_data.get('last_name')
        country = serializer_data.get('country')
        address = serializer_data.get('address')
        zip_code = serializer_data.get('zip_code')
        city = serializer_data.get('city')
            
            
        return{
            'is_client': is_student,
            'is_staff': is_staff,
            'email': email,
            'username': username,
            'btc_wallet': btc_wallet,
            'monthjoined': date,
            'hash': urlhash,
            'balance': balance,
            'last_login': last_login,
            'Link':ref,
            'compounding':compounding,
            "referral": referral,
            "last_login": last_login,
            "activeA": activeA,
            "activeP": activeP,
            "first_name": first_name,
            "last_name": last_name,
            "country": country,
            "address": address,
            "zip_code": zip_code,
            "city": city,
            "email_verified": email_verified,
            "withdrawn": withdrawn
            
        }

    