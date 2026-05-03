from django.urls import path
from .views import RegistrationView, CustomLoginView, BoardListView, BoardDetailView
from rest_framework import routers

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('boards/', BoardListView.as_view()),
    path('boards/<int:pk>/', BoardDetailView.as_view()),
]
