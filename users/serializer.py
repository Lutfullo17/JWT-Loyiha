from django.utils.lorem_ipsum import paragraph
from rest_framework import serializers, status
from setuptools.config.pyprojecttoml import validate
from telebot.util import validate_web_app_data

from .models import CustomUser, VIA_EMAIL, VIA_PHONE, CODE_VERIFY, DONE, PHOTO_DONE, Post, Like, Commit, Story, Follow, StoryView
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from shered.utility import check_email_or_phone, send_verification_email, check_email_or_phone_or_username
from django.contrib.auth import authenticate

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
    def auth_validate(data):
        user_input = data.get('email_or_phone')
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

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if password is None or confirm_password is None or password != confirm_password:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Parollar mos emas yoki xato kiritildi'
            }
            raise ValidationError(response)
        if len([i for i in password if i == ' ']) > 0:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Parollar xato kiritildi'
            }
            raise ValidationError(response)

        return data

    def validate_username(self, username):
        if len(username) < 6:
            raise ValidationError({'message': 'Username kamida 7 ta bolishi kerak'})
        elif not username.isalnum():
            raise ValidationError({'message': 'Username da ortiqcha belgilar bolmasligi kerak'})
        elif username[0].isdigit():
            raise ValidationError({'message': 'Username raqam bilan boshlanmasin'})
        return username

    def validate_first_name(self,first_name):
        first_name = first_name.strip()
        if not first_name:
            raise serializers.ValidationError("Ism bo'sh bo'lishi mumkin emas.")
        if len(first_name) < 3:
            raise serializers.ValidationError("Ism kamida 3 ta belgidan iborat bo'lishi kerak.")
        if len(first_name) > 50:
            raise serializers.ValidationError("Ism 50 ta belgidan oshmasligi kerak.")
        if not first_name.isalpha():
            raise serializers.ValidationError("Ism faqat harflardan iborat bo'lishi kerak.")
        return first_name.capitalize()

    def validate_last_name(self, last_name):
        last_name = last_name.strip()
        if not last_name:
            raise serializers.ValidationError("Familiya bo'sh bo'lishi mumkin emas.")
        if len(last_name) < 2:
            raise serializers.ValidationError("Familiya kamida 2 ta belgidan iborat bo'lishi kerak.")
        if len(last_name) > 50:
            raise serializers.ValidationError("Familiya 50 ta belgidan oshmasligi kerak.")
        if not last_name.isalpha():
            raise serializers.ValidationError("Familiya faqat harflardan iborat bo'lishi kerak.")
        return last_name.capitalize()

    def update(self, instance, validated_data):
        if instance.auth_status != CODE_VERIFY:
            raise ValidationError({"message": "siz hali tasdiqlanmagansiz ",'status':status.HTTP_400_BAD_REQUEST})
        instance.first_name = validated_data.get('first_name')
        instance.last_name = validated_data.get('last_name')
        instance.username = validated_data.get('username')
        instance.set_password(validated_data.get('password'))
        instance.auth_status = DONE
        instance.save()
        return instance


class UserPhotoStatusSerializer(serializers.Serializer):
    photo = serializers.ImageField()

    def update(self, instance, validated_data):
        photo = validated_data.get('photo', None)
        if photo:
            instance.photo = photo
        if instance.auth_status == DONE:
            instance.auth_status = PHOTO_DONE
        instance.save()

        return instance


class LoginSerializer(TokenObtainPairSerializer):
    password = serializers.CharField(required=True, write_only=True)

    def __init__(self,  *args,**kwargs,):
        super().__init__(*args, **kwargs)
        self.fields['user_input'] = serializers.CharField(required=True, write_only=True)
        self.fields['username'] = serializers.CharField(read_only=True)

    def validate(self, attrs):
        user = self.check_user_type(attrs)

        data = {
            "refresh": user.token()['refresh'],
            "access": user.token()['access'],
            "user": {
                "username": user.username,
                "email": user.email
            }
        }

        return data

    def check_user_type(self,data):
        password=data.get('password')
        user_input=data.get('user_input')
        user_input_type=check_email_or_phone_or_username(user_input)
        print(user_input_type, "+++++++++++-------------")
        if user_input_type=='username':
            user=CustomUser.objects.filter(username=user_input).first()
            self.get_object(user)
            username=user.username
        elif user_input_type=='email':
            user=CustomUser.objects.filter(email=user_input).first()
            self.get_object(user)
            print(user, "-------------------")
            username=user.username

        elif user_input_type=='phone':
            user=CustomUser.objects.filter(phone_number=user_input).first()
            self.get_object(user)
            username=user.username
        else:
            raise ValidationError(detail='Malumot topilmadi')


        authentication_kwargs={
            "password":password,
            self.username_field:username
        }

        if user.auth_status not in [DONE, PHOTO_DONE]:
            raise ValidationError(detail="Siz hali to'liq ruyxatdan utmagansiz")

        user = authenticate(**authentication_kwargs)

        if not user:
            raise ValidationError('Login va parol xato')

        return user

    def get_object(self, user):

        if not user:
            raise ValidationError({'message': 'Login Xato malumot', 'status': status.HTTP_400_BAD_REQUEST})
        return True

class ForgotPasswordSerializer(serializers.Serializer):
    user_input = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        user_data = attrs.get('user_input', None)
        if not user_data:
            raise ValidationError("Email, Telefon raqam va username kiritng")
        user_data_type = check_email_or_phone_or_username(user_data)
        user = CustomUser.objects.filter(Q(username=user_data)| Q(email=user_data) | Q(phone_number=user_data))


        if not user:
            raise ValidationError("Email, Telefon raqam va username xato ")

        if user and user_data_type == 'username':
            if user.email:
                code = user.generate_code()
                print("E CODE++++++", code)
            elif user.phone_number:
                code = user.generate_code()
                print("P  CODE++++++", code)
            else:
                print("Siz toliq utmagansiz")

        elif user and user_data_type == 'email':
            code = user.generate_code()
            print("P  CODE++++++", code)
        elif user and user_data_type == 'phone':
            code = user.generate_code()
            print("P  CODE++++++", code)
        response_data = {
            'status': status.HTTP_201_CREATED,
            'message': "Kod yuborildi"
        }
        return response_data




class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise ValidationError("Parollar bir-biriga mos kelmadi.")
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data.get('password'))
        instance.save()
        return instance




class PostSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True)
    desc = serializers.CharField(required=True)
    image = serializers.ImageField(required=True)

    def validate(self, attrs):
        if len(attrs['title']) <  3:
            raise ValidationError('title kamida 3 ta bulish kerak')

    def create(self, validated_data):
        user = self.context['request'].user

        post = Post.objects.create(user=user,
                title=validated_data.get('title'),
                desc=validated_data.get('desc'),
                image=validated_data.get('image'),
        )
        return post




class CommitSerializer(serializers.ModelSerializer):
    post = serializers.IntegerField(required=True)
    text = serializers.CharField(required=True)
    parent = serializers.IntegerField(required=True, allow_null=True)

    def validate(self, attrs):
        post_id = attrs.get('post')
        parent_id = attrs.get('parent')

        post = Post.objects.filter(id=post_id).first()
        if not post:
            raise ValidationError("post topilmadi")

        if parent_id:
            parent = Commit.objects.filter(id=parent_id).first()
            if not parent:
                raise ValidationError("Parent commit topilmadi")
            if parent.post.id != post_id:
                raise ValidationError("Parent boshqa postga tegishli")

        return attrs


    def create(self, validated_data):
        user = self.context['request'].user

        commit = Commit.objects.create(
            user=user,
            post_id=validated_data.get('post'),
            text = validated_data.get('text'),
            parent_id= validated_data.get('parent')
        )
        return commit



class LikeSerializer(serializers.ModelSerializer):
    post = serializers.IntegerField(required=True)

    def validate(self, attrs):
        post = Post.objects.filter(id=attrs.get('post')).first()
        if not post:
            raise ValidationError('Post Topilmadi')
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        post_id = validated_data.get('post')

        like = Like.objects.filter(user=user, post_id=post_id).first()

        if like:
            like.delete()
            return {"status": "unliked"}
        else:
            Like.objects.create(user=user, post_id=post_id)
            return {"status": "liked"}
