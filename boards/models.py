from django.db import models

from auth_app.models import User, UserProfile


class Board(models.Model):
    title = models.CharField(max_length=255)
    member = models.ManyToManyField(UserProfile, related_name="boards")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title