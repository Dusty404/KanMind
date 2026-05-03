from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    fullname = models.CharField(max_length=150)

    def __str__(self):
        return self.fullname
    
class Board(models.Model):
    title = models.CharField(max_length=255)
    member = models.ManyToManyField(UserProfile, related_name="boards")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

class Task(models.Model):
    STATUS_CHOICES = [
        ("to_do", "To do"),
        ("in_progress", "In progress"),
        ("review", "Review"),
        ("done", "Done"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    title = models.CharField(max_length=255)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="to_do")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium")