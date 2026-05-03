from django.urls import path
from .views import BoardListAndCreateView, BoardDetailView

urlpatterns = [
    path('boards/', BoardListAndCreateView.as_view()),
    path('boards/<int:pk>/', BoardDetailView.as_view()),
]
