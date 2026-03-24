from django.db.models.expressions import result
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework import permissions, status
from rest_framework.utils.representation import serializer_repr
from yaml import serialize

from .serializer import (SignUpSerializer, UserChangeInfoSerializer, UserPhotoStatusSerializer , LoginSerializer, ResetPasswordSerializer, \
            ForgotPasswordSerializer, PostSerializer, CommitSerializer, LikeSerializer, FollowSerializer, StorySerializer, StoryViewSerializer)
from .models import (CustomUser,
    NEW, CODE_VERIFY, DONE, PHOTO_DONE, VIA_PHONE, VIA_EMAIL, CodeVerify, Post, Commit, Like, Story, StoryView, Follow
    )
from rest_framework.views import APIView
from datetime import datetime
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken



class SingUpView(CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignUpSerializer
    queryset = CustomUser


class CodeVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        user = request.user
        code = self.request.data.get('code')
        codes  =CodeVerify.objects.filter(code = code, expiration_time__gte = datetime.now(), is_active = True)
        print(codes)
        if codes.exists():
            raise ValidationError({'message': 'Kodingiz  xato yoki eskirgan', 'status': status.HTTP_400_BAD_REQUEST})
        else:
            codes.update(is_active = False)

        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFY
            user.save()

        response_data = {
            'message': 'kod tasdiqlandi',
            'status': status.HTTP_200_OK,
            'access': user.token()['access'],
            'refresh': user.token()['refresh']
        }
        return Response(response_data)


class GetNewCodeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        user = request.user
        code = CodeVerify.objects.filter(user = user, expiration_time__gte = datetime.now(), is_active = True)
        if code.exists():
            raise ValidationError({'message': 'sizda hali active kod bor', 'status': status.HTTP_400_BAD_REQUEST})
        else:
            if user.auth_type == VIA_EMAIL:
                code = user.generate_code(VIA_EMAIL)
                print(code, '|||||||||||||||||||||')
            elif user.auth_type == VIA_PHONE:
                code = user.generate_code(VIA_PHONE)
                print(code, '||||||||||||||||||||||||||||||')

        response_data = {
            'message': 'kod Yuborildi',
            'status': status.HTTP_201_CREATED
        }
        return Response(response_data)


class UserChangeInfoView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    def put(self, request):
        user = request.user
        serializer = UserChangeInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user, validated_data=serializer.validated_data)

        response = {
            'message': 'Malumotlar qoshildi',
            'status': status.HTTP_200_OK,
            'access': user.token()['access'],
            'refresh': user.token()['refresh'],
        }
        return Response(response)


class UserChangePhotoView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    def patch(self, request):
        user = request.user
        serializer = UserPhotoStatusSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user, validated_data=serializer.validated_data)

        response = {
            'message': 'Photo qoshildi',
            'status': status.HTTP_200_OK,
            'access': user.token()['access'],
            'refresh': user.token()['refresh'],
        }
        return Response(response)

class Login(TokenObtainPairView):
    serializer_class = LoginSerializer

class Logout(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        refresh= self.request.data.get('refresh', None)
        try:
            refresh_token = RefreshToken(refresh)
            refresh_token.blacklist()
        except Exception as e:
            raise ValidationError(detail=f"Xatolik: {e}")

        else:
            response_data = {
                'status': status.HTTP_200_OK,
                'message': 'Tizimdan chiqdingiz'
            }
            return Response(response_data)


class LoginRefresh(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        refresh = self.request.data.get('refresh', None)
        try:
            refresh_token = RefreshToken(refresh)
            refresh_token.blacklist()
        except Exception as e:
            raise ValidationError(detail=f"Xatolik: {e}")

        else:
            response_data = {
                'status': status.HTTP_201_CREATED,
                'access': str(refresh_token.access_token)
            }
            return Response(response_data)


class ForgotPasswordView(APIView):

    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        user = self.request.user
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response({
                "status": True,
                "message": "Kod yuborildi",
                'access': user.token()['access'],
                'refresh': user.token()['refresh'],

            }, status=status.HTTP_200_OK)



class ResetPasswordView(UpdateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = (permissions.AllowAny,)


    def get_object(self):
        return self.request.user


    def update(self, request, *args, **kwargs):
        user = self.get_object()
        if user.auth_status != CODE_VERIFY:
            raise ValidationError("Avval kodni tasdiqlash kerak")
        serializer = self.get_serializer(user, data= request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user.auth_status = DONE
        user.save()

        return Response({
            'status': True,
            'message': "Parol o'zgartirildi",
            'access': user.token()['access'],
            'refresh': user.token()['refresh']
        }, status=status.HTTP_200_OK)


class PostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        post = Post.objects.all().order_by('-id')
        serializer = PostSerializer(post, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = PostSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        return Response({
            "id": post.id,
            "message": "Post yaratildi"
        }, status=201)



class CommitAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        commits = Commit.objects.all().order_by('-id')
        serializer = CommitSerializer(commits, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = CommitSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        commit = serializer.save()
        return Response({
            "id": commit.id,
            "message": "Commit qo'shildi"
        }, status=201)



class LikeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LikeSerializer(data= request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result)



class FollowAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FollowSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result =serializer.save()
        return Response(result)



class StoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stories = Story.objects.all().order_by('-id')
        serializer = StorySerializer(stories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StorySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        story = serializer.save()
        return Response({"id": story.id, "message": "Story joylandi"}, status=201)


class StoryViewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = StorySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result)

