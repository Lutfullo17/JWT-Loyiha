import re
from re import fullmatch
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
import random
from users.models import CodeVerify,VIA_EMAIL
from datetime import datetime

email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
phone_regex = re.compile(r'^998([378][2]|(9[013-57-9]))\d{7}$')

def check_email_or_phone(user_input):
    print(user_input, '|||||||||||||||||||||||||||||||||')
    if fullmatch(phone_regex, user_input):
        return 'phone'
    elif fullmatch(email_regex, user_input):
        return 'email'
    else:

        raise ValidationError({
            'status': status.HTTP_400_BAD_REQUEST,
            'message': "Email yoki telefon raqamingiz xato kiritilgan"

        })

def send_verification_email(user):
    active_codes = CodeVerify.objects.filter(user=user, expiration_time__gte=datetime.now())
    if active_codes.exists():
        raise ValidationError({'message': 'sizda active code bor'})
    code = random.randint(1000, 9999)
    CodeVerify.objects.create(
        code=str(code),
        user=user,
        verify_type=VIA_EMAIL
    )
    subject = "Email tasdiqlash kodi"
    message = (
        f"Assalomu alaykum!\n\n"
        f"Ro'yxatdan o'tish uchun tasdiqlash kodingiz: {code}\n\n"
        f"Kod {settings.EMAIL_EXPIRATION_TIME} daqiqa davomida amal qiladi.\n\n"
        f"Agar siz ro'yxatdan o'tmagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring."
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        raise ValidationError({'message': 'Xato email'})








