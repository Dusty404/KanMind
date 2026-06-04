from django.urls import include, path
from rest_framework import routers

from .views import BoardViewSet, EmailCheckView


router = routers.SimpleRouter()
router.register(r"boards", BoardViewSet, basename="boards")

urlpatterns = [
    path("email-check/", EmailCheckView.as_view()),
    path("", include(router.urls)),
]