from django.urls import path, include
from .views import BoardViewSet, EmailCheckView, TasksViewSet
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'boards', BoardViewSet, basename='boards')
router.register(r'tasks', TasksViewSet, basename='tasks')

urlpatterns = [
    path('', include(router.urls)),
    path('<str:email>-check/', EmailCheckView.as_view())
]
