from django.urls import path
from .views import SingUpView, CodeVerifyView, GetNewCodeView, UserChangeInfoView, UserChangePhotoView, Login, Logout

urlpatterns = [
    path('signup/', SingUpView.as_view()),
    path('code-verify/', CodeVerifyView.as_view()),
    path('get-new-code/', GetNewCodeView.as_view()),
    path('change-info/', UserChangeInfoView.as_view()),
    path('change-photo/', UserChangePhotoView.as_view()),
    path('login/', Login.as_view()),
    path('logout/', Logout.as_view()),
]