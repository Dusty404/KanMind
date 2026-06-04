from django.urls import path

from .views import CommentsView

urlpatterns = [
    path("tasks/<int:task_id>/comments/", CommentsView.as_view()),
    path("tasks/<int:task_id>/comments/<int:comment_id>/", CommentsView.as_view()),
]
