from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Chat(models.Model):
    members = models.ManyToManyField(User, blank=True)
    title = models.CharField(max_length=100, null=False, blank=False, help_text="Title of the Chat")

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(max_length=1000, null=False, blank=True, default="", help_text="User Message")


# Neues Modell Post
class Post(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title