"""
Serializers for handling user authentication, registration,
and profile data within the auth_app.
"""
from rest_framework import serializers
from user_auth_app.models import UserProfile
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Validates that passwords match and that the email and username are unique before
    creating a new User and associated UserProfile instance.

    Fields:
        id (int): User ID (read-only).
        username (str): Full name of the user (used to construct first and last name).
        email (str): Email address of the user.
        password (str): Password (write-only).
        repeated_password (str): Password confirmation (write-only).
        type (str): User type (either 'customer' or 'business').
    """
    email = serializers.EmailField(required=True)
    repeated_password = serializers.CharField(write_only=True)
    username = serializers.CharField(write_only=True, allow_blank=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def create(self, validated_data):
        """
        Creates a new User instance after validating the input data.

        Ensures that the provided passwords match, and that both the email and username are unique.
        Automatically splits the username into first and last name components.

        Args:
            validated_data (dict): The validated user input data.

        Returns:
            User: The newly created user instance.
        """
        pw = validated_data.pop('password')
        repeated_pw = validated_data.pop('repeated_password')
        username = validated_data.pop('username').title()

        if pw != repeated_pw:
            raise serializers.ValidationError({'error': 'Passwords do not match'})

        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError({'error': 'This email is already taken'})
        
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'error': 'This username is already taken'})

        names = username.split()
        first_name = names[0] if len(names) > 0 else ""
        last_name = " ".join(names[1:]) if len(names) > 1 else ""

        account = User(
            email=validated_data['email'],
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        account.set_password(pw)
        account.save()

        UserProfile.objects.create(user=account)

        return account
    

class UsernameAuthTokenSerializer(serializers.Serializer):
    """
    Serializer for authenticating a user using username and password.
    """
    username = serializers.CharField(label="Username", write_only=True)
    password = serializers.CharField(label="Password", style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        """
        Validates the username and password credentials.

        Ensures both fields are provided and authenticates the user.
        Raises a validation error if authentication fails.

        Args:
            attrs (dict): Incoming data with username and password.

        Returns:
            dict: Validated data including authenticated user instance.
        """
        username = attrs.get('username')
        password = attrs.get('password')

        if not username or not password:
            raise serializers.ValidationError("Must include 'username' and 'password'.")

        user = authenticate(self.context.get('request'), username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        attrs['user'] = user
        return attrs
    