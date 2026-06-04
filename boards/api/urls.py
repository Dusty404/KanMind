from django.urls import include, path
from rest_framework import routers

from .views import (BoardViewSet)


router = routers.SimpleRouter()
router.register(r"boards", BoardViewSet, basename="boards")

urlpatterns = [
    path("", include(router.urls)),
]