from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from shered.models import BaseModel
from datetime import datetime, timedelta
from django.utils import timezone
from config.settings import EMAIL_EXPIRATION_TIME, PHONE_EXPIRATION_TIME
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
import random

# User roles
ORDINARY_USER, ADMIN, MANAGER = 'ordinary_user', 'admin', 'manager'
NEW, CODE_VERIFY, DONE, PHOTO_DONE = 'new', 'code_verify', 'done', 'photo_done'
VIA_EMAIL, VIA_PHONE = 'via_email', 'via_phone'


class CustomUser(AbstractUser, BaseModel):

    USER_ROLES = (
        (ORDINARY_USER, ORDINARY_USER),
        (ADMIN, ADMIN),
        (MANAGER, MANAGER)
    )

    # Auth status
    AUTH_STATUS = (
        (NEW, NEW),
        (CODE_VERIFY, CODE_VERIFY),
        (DONE, DONE),
        (PHOTO_DONE, PHOTO_DONE)
    )

    # Auth type
    AUTH_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE)
    )

    user_role = models.CharField(max_length=20, choices=USER_ROLES, default=ORDINARY_USER)
    auth_status = models.CharField(max_length=20, choices=AUTH_STATUS, default=NEW)
    auth_type = models.CharField(max_length=20, choices=AUTH_TYPE)

    email = models.EmailField(max_length=50, unique=True, blank=False, null=False)
    phone_number = models.CharField(max_length=13, blank=True, null=True, unique=True)
    photo = models.ImageField(
        upload_to='user_photo/',
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'heic'])],
        blank=True, null=True
    )

    def __str__(self):
        return self.username

    # Username generatsiyasi agar bo'sh bo'lsa
    def generate_username(self):
        if not self.username:
            temp_username = f"user{uuid.uuid4().__str__().split('-')[-1]}"
            while CustomUser.objects.filter(username=temp_username).exists():
                temp_username += str(random.randint(0, 9))
            self.username = temp_username

    def check_pass(self):
        if not self.password:
            temp_password = f"pass{uuid.uuid4().__str__().split('-')[-1]}"

            self.set_password(temp_password)


    # Emailni normalize qilish
    def normalize_email(self):
        if self.email:
            self.email = self.email.lower()

    # JWT token generatsiyasi
    def token(self):
        refresh_token = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh_token),
            'access': str(refresh_token.access_token)
        }

    # Code verify yaratish
    def generate_code(self, verify_type):
        code = random.randint(1000, 9999)
        CodeVerify.objects.create(
            code=code,
            user=self,
            verify_type=verify_type
        )
        return code

    # Clean method
    def clean(self):
        self.generate_username()
        self.normalize_email()
        self.check_pass()
        return super().clean()

    # Save method
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# Verification codes
class CodeVerify(BaseModel):
    VERIFY_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE)
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verify_codes')
    code = models.CharField(max_length=4)
    verify_type = models.CharField(max_length=30, choices=VERIFY_TYPE)
    expiration_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = timezone.now() + timedelta(minutes=EMAIL_EXPIRATION_TIME)
        else:
            self.expiration_time = timezone.now() + timedelta(minutes=PHONE_EXPIRATION_TIME)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} | {self.code}"

    class CodeVerify(BaseModel):
        VERIFY_TYPE = (
            (VIA_EMAIL, VIA_EMAIL),
            (VIA_PHONE, VIA_PHONE),
        )

        user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verify_codes')
        code = models.CharField(max_length=4)
        verify_type = models.CharField(max_length=30, choices=VERIFY_TYPE)
        expiration_time = models.DateTimeField()
        is_active = models.BooleanField(default=True)

        def save(self, *args, **kwargs):
            if self.verify_type == VIA_EMAIL:
                minutes = getattr(settings, 'EMAIL_EXPIRATION_TIME', 5)
            else:
                minutes = getattr(settings, 'PHONE_EXPIRATION_TIME', 2)
            self.expiration_time = datetime.now() + timedelta(minutes=minutes)
            super().save(*args, **kwargs)

        def __str__(self):
            return f"{self.user} - {self.code}"