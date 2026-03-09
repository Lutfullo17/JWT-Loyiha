from django.urls import path
from .views import SingUpView, CodeVerifyView, GetNewCodeView

urlpatterns = [
    path('signup/', SingUpView.as_view()),
    path('code-verify/', CodeVerifyView.as_view()),
    path('get-new-code/', GetNewCodeView.as_view()),
]