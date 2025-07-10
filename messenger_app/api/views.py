from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from messenger_app.api.serializers import ChatSerializer, PostSerializer
from rest_framework import viewsets
from rest_framework.response import Response
from messenger_app.models import Post
            
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
