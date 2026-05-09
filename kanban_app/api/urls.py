from django.urls import path, include
from .views import BoardViewSet
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'boards', BoardViewSet, basename='boards')

urlpatterns = [
    path('', include(router.urls)),
]
