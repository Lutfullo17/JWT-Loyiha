from rest_framework import serializers, status
from .models import CustomUser, VIA_EMAIL, VIA_PHONE, CODE_VERIFY, DONE
from rest_framework.exceptions import ValidationError
from django.db.models import Q
import re
from shered.utility import check_email_or_phone, send_verification_email


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_status = serializers.CharField(read_only=True)
    auth_type = serializers.CharField(read_only=True)
    email_or_phone = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'auth_status', 'auth_type','email_or_phone']

    def create(self, validated_data):
        validated_data.pop('email_or_phone',None)
        user = CustomUser.objects.create(**validated_data)
        if user.auth_type == VIA_EMAIL:
            code =send_verification_email(user)
            print(code, '|||||||||||||||||||||')
        elif user.auth_type == VIA_PHONE:
            code = user.generate_code(VIA_PHONE)
            print(code, '|||||||||=========================|')
        else:
            raise ValidationError('Email yoki telefon raqam xato')

        return user
    def validate(self, attrs):
        super().validate(attrs)
        data = self.auth_validate(attrs)
        return data


    @staticmethod
    def auth_validate(user_input):
        user_input = user_input.get('email_or_phone')
        user_input_type = check_email_or_phone(user_input)
        if user_input_type == 'phone':
            data = {
                'auth_type': VIA_PHONE,
                'phone_number': user_input
            }
        elif user_input_type == 'email':
            data = {
                'auth_type': VIA_EMAIL,
                'email': user_input
            }
        else:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': "email yoki telefon raqamiz xato"
            }
            raise ValidationError(response)
        return data


    def validate_email_or_phone(self, email_or_phone):
        user = CustomUser.objects.filter(Q(phone_number=email_or_phone) | Q(email=email_or_phone))
        if user:
            raise ValidationError({'message': 'email yoki tel raqam band!'})
        return email_or_phone

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tokens = instance.token()
        data['message'] = 'Tasdiqlash kodi yuborildi.'
        data['refresh'] = tokens['refresh']
        data['access'] = tokens['access']
        return data



class UserChangeInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError('Parollar mos emas')


    def validate_username(self, username):
        if re.match(r'^[a-z]+$', username):
            raise serializers.ValidationError('Username xato')



    def validated_first_name(value):
        if re.match(r'^[a-zA-Z]+$', value):
            raise serializers.ValidationError('Firstname Faqat harf bulish kerak')


    def validated_last_name(value):
        if re.match(r'^[a-zA-Z]+$', value):
            raise serializers.ValidationError('Lastname Faqat harf bulish kerak')

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name')
        instance.last_name = validated_data.get('last_name')
        instance.username = validated_data.get('username')

        instance.password.set_password(validated_data.get('password'))
        if instance.auth_status != CODE_VERIFY:
            raise ValidationError({'message': 'Siz hali tasdiqlanmagansiz', 'status': status.HTTP_400_BAD_REQUEST})
        instance.auth_status = DONE
        instance.save()

        return instance

