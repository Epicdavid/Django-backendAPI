import string
import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from allauth.account.signals import user_signed_up
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime
from simple_history.models import HistoricalRecords
from django.dispatch import receiver
from pinax.referrals.models import Referral
from mptt.models import (
    MPTTModel,
    TreeForeignKey

)
from django.urls import reverse_lazy



# Create your models here.

class User(AbstractUser):
    first_name = models.CharField(max_length=300,blank=True, null=True)
    last_name  = models.CharField(max_length=300,blank=True, null=True)
    address = models.CharField(max_length=300,blank=True, null=True)
    city = models.CharField(max_length=200,blank=True, null=True)
    country = models.CharField(max_length=200,blank=True, null=True)
    zip_code =models.IntegerField(blank=True, null=True)
    is_student = models.BooleanField(default=False)
    btc_wallet = models.CharField(max_length=300)
    date_joined = models.DateTimeField(auto_now_add=True)
    urlhash = models.CharField(max_length=14, null=True, blank=True, unique=True)
    account_balance = models.DecimalField(max_digits=15, decimal_places=0, default=0,)
    active_affiliates = models.CharField(max_length=200, default=0)
    active_package = models.CharField(max_length=300,blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    compounding = models.BooleanField(default=False)
    totalWithdrawn = models.DecimalField(max_digits=15,decimal_places=2, default=0)
    
    
    def __str__(self):
        return self.username

    def monthjoined(self):
        return self.date_joined.strftime('%Y')
    
   
    def id_generator(size=14, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def save(self,*args, **kwargs):
        if not self.urlhash:
            # Generate ID once, then check the db. If exists, keep trying.
            self.urlhash = User.id_generator()
            while User.objects.filter(urlhash=self.urlhash).exists():
                self.urlhash = User.id_generator()
        super().save(*args, **kwargs)



class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='user',
        related_name="profile"
    )
    referral = models.OneToOneField(
        Referral,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='referral',
    )
    referredBy = models.ForeignKey(User, related_name='referredBy', on_delete=models.CASCADE, blank=True, null=True)
   



    def __str__(self):
        return self.user.username

        


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
    


@receiver(user_signed_up)
def handle_user_signed_up(sender, request, user, **kwargs):
    profile = user.profile
    referral = Referral.create(user=user, redirect_to=reverse_lazy('rest_register'))
    profile.referral = referral
    action = Referral.record_response(request, "USER_SIGNUP")
    if action is not None:
            referra = Referral.objects.get(id=action.referral.id)
            print(referra.user.id)
            profile.referredBy = User.objects.get(id=referra.user.id)
            profile.save()
    profile.save()        