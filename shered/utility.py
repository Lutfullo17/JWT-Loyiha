import re
from http.client import responses
from re import fullmatch
from rest_framework import status
from rest_framework.exceptions import ValidationError



phone_regex = re.compile(r'/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/')
email_regex = re.compile(r'/^998(9[012345789]|6[125679]|7[01234569])[0-9]{7}$/')

def check_email_or_pphone(user_input):
    if fullmatch(phone_regex, user_input):
        data = 'phone'
    elif fullmatch(email_regex, user_input):
        data = 'email'
    else:
        response = {
            'status' : status.HTTP_400_BAD_REQUEST,
            'message': "Email yoki telefon raqamingiz xato kiritilgan"
        }
        raise ValidationError(response)
    return data














