from rest_framework import serializers
from messenger_app.models import Chat, Post

class ChatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chat
        exclude = ("id")
        read_only_fields = [
            "author"
        ]

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ['author']


