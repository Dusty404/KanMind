from django.urls import include, path
from rest_framework import routers

from .views import (
    ReviewingView,
    TasksAssignedToUserView,
    TasksViewSet,
)


router = routers.SimpleRouter()
router.register(r"tasks", TasksViewSet, basename="tasks")

urlpatterns = [
    path("tasks/assigned-to-me/", TasksAssignedToUserView.as_view()),
    path("tasks/reviewing/", ReviewingView.as_view()),
    path("", include(router.urls)),
]