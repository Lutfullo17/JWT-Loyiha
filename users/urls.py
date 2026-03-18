from django.urls import path
from .views import SingUpView, CodeVerifyView, GetNewCodeView, UserChangeInfoView, UserChangePhotoView,  Login, Logout, LoginRefresh, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path('signup/', SingUpView.as_view()),
    path('code-verify/', CodeVerifyView.as_view()),
    path('get-new-code/', GetNewCodeView.as_view()),
    path('change-info/', UserChangeInfoView.as_view()),
    path('change-photo/', UserChangePhotoView.as_view()),
    path('login/', Login.as_view()),
    path('logout/', Logout.as_view()),
    path('refresh/', LoginRefresh.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
]