from django.urls import path
from .views import RegistrationView, CustomLoginView, LogoutView

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout')
]