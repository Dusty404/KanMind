from django.urls import path, include
from .views import BoardViewSet, EmailCheckView, TasksViewSet, TasksAssignedToUserView, ReviewingView, CommentsView
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'boards', BoardViewSet, basename='boards')
router.register(r'tasks', TasksViewSet, basename='tasks')

urlpatterns = [
    path('tasks/assigned-to-me/', TasksAssignedToUserView.as_view()),
    path('tasks/reviewing/', ReviewingView.as_view()),
    path("tasks/<int:task_id>/comments/", CommentsView.as_view()),
    path("tasks/<int:task_id>/comments/<int:comment_id>/", CommentsView.as_view()),
    path('email-check/', EmailCheckView.as_view()),
    path('', include(router.urls)),
]
