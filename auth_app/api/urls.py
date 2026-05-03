from django.urls import path
from .views import RegistrationView, CustomLoginView, BoardListView, BoardDetailView
from rest_framework import routers

#router = routers.SimpleRouter()
#router.register(r'boards', BoardsViewSet)

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
]
