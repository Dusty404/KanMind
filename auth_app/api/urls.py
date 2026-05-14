from django.urls import path
from .views import RegistrationView, CustomLoginView

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
]