
from rest_framework.generics import CreateAPIView
from rest_framework import permissions, status
from .serializer import SignUpSerializer
from .models import (CustomUser,
    NEW, CODE_VERIFY, DONE, PHOTO_DONE,
    VIA_PHONE, VIA_EMAIL,
    CodeVerify
    )
from rest_framework.views import APIView
from datetime import datetime
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response



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


