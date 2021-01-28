from django.shortcuts import render
from django.views.generic.base import TemplateView
from allauth.account.signals import email_confirmed
from django.dispatch import receiver
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.mixins import UpdateModelMixin
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist

from allauth.account.utils import send_email_confirmation
from rest_framework.decorators import api_view
from .models import * 
from . import serializers
import json
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.response import Response

from rest_framework.generics import get_object_or_404
from allauth.account.admin import EmailAddress

from rest_auth.views import LoginView
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from rest_auth.registration.serializers import VerifyEmailSerializer,RegisterSerializer
from rest_auth.serializers import PasswordResetSerializer
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView
from rest_framework.exceptions import APIException

from rest_auth.models import TokenModel
from django.conf import settings
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

@api_view()
def django_rest_auth_null():
    return Response(status=status.HTTP_400_BAD_REQUEST)

class UserDetailsView(ObtainAuthToken):
  
    def get(self, request, *args, **kwargs):
        token = Token.objects.get(key=request.data['token'])
        return Response({'token': token.key, 'id': token.user_id})

class Contact(APIView):

    def post(self, request, *args, **kwargs):
        serializer_class = serializers.Contact(data=request.data)
        if serializer_class.is_valid():
             data = serializer_class.validated_data
             sender_email = data.get('email')
             sender_name = data.get('name') 
             message = "{0} from {1} has sent you a new message:\n\n{2}.\n\n Phone: {3}".format(sender_name,sender_email, data.get('message'),data.get('phone'))
             send_mail('New Enquiry', message, "support@domain.com", ['support@domain.com'])
             return Response({"success": "Your message has been sent, we will be in touch shortly"})
        return Response({'success': "Failed"}, status=status.HTTP_400_BAD_REQUEST)     


class UserPartialUpdateView(GenericAPIView, UpdateModelMixin):
    
    '''
    You just need to provide the field which is to be modified.
    '''
    authentication_classes = [TokenAuthentication] 
    queryset = User.objects.all()
    serializer_class = serializers.UpdateUserSerializer
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        serializer.save()
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
          
          return self.partial_update(request, *args, **kwargs)    





class EmailView(TemplateView):

    template_name = "account/email/email_confirmation_signup_message.html"

@receiver(email_confirmed)
def email_confirmed_(request, email_address, **kwargs):
    user = email_address.user
    user.email_verified = True

    user.save()

# request a new confirmation email
class EmailConfirmation(APIView):
     

    def post(self, request):
        if request.user.email_verified:
            return Response({'message': 'Email already verified'}, status=status.HTTP_201_CREATED)

        send_email_confirmation(request, request.user)
        return Response({'message': 'Email confirmation sent'}, status=status.HTTP_201_CREATED)    

@csrf_exempt
def validateEmailToken(request):
    d = json.loads(request.body)
    data = d['body']
    print(data['token'])
    token = data['token']
    res = {
        'status': 'success',
        'message': 'Valid',
    }
    
    if User.objects.filter(email_verified_hash=token, email_verified=0).exists():
        tokenExists = User.objects.get(email_verified_hash=token, email_verified=0)

        tokenExists.email_verified = 1
        tokenExists.save()

    else:
        res = {
            'status': 'failed',
            'message': 'Invalid',
        }
    
    return JsonResponse(res) 

class PasswordResetView(GenericAPIView):
    """
    Calls Django Auth PasswordResetForm save method.
    Accepts the following POST parameters: email
    Returns the success/fail message.
    """
    serializer_class = serializers.PasswordResetSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        # Return the success message with OK HTTP status
        return Response(
            {"detail": _("Password reset e-mail has been sent.")},
            status=status.HTTP_200_OK
        )

class VerifyEmailView(GenericAPIView):

    def get_serializer(self, *args, **kwargs): 
        return VerifyEmailSerializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.kwargs['key'] = serializer.validated_data['key']
        try:
            confirmation = self.get_object()
            confirmation.confirm(self.request)
            return Response({'detail': _('Successfully confirmed email.')}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'detail': _('Error. Incorrect key.')}, status=status.HTTP_400_BAD_REQUEST)

    def get_object(self, queryset=None):
        key = self.kwargs['key']
        emailconfirmation = EmailConfirmationHMAC.from_key(key)
        if not emailconfirmation:
            if queryset is None:
                queryset = self.get_queryset()
            try:
                emailconfirmation = queryset.get(key=key.lower())
            except EmailConfirmation.DoesNotExist:
                raise EmailConfirmation.DoesNotExist
        return emailconfirmation

    def get_queryset(self):
        qs = EmailConfirmation.objects.all_valid()
        qs = qs.select_related("email_address__user")
        return qs    

class NewEmailConfirmation(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        user = get_object_or_404(User, email=request.data['email'])
        emailAddress = EmailAddress.objects.filter(user=user, verified=True).exists()

        if emailAddress:
            return Response({'message': 'This email is already verified'}, status=status.HTTP_200_OK)
        else:
            try:
                send_email_confirmation(request, user=user)
                return Response({'message': 'Email confirmation sent'}, status=status.HTTP_200_OK)
            except APIException:
                return Response({'message': 'This email does not exist, please create a new account'}, status=status.HTTP_200_OK)

