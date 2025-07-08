from rest_framework import generics, status
from django.contrib.auth.models import User
from user_auth_app.models import UserProfile
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from user_auth_app.api.serializers import RegistrationSerializer, UsernameAuthTokenSerializer


class RegistrationView(APIView):
    """
    API view to register a new user and return authentication token.

    Accepts user data, creates a new user upon validation,
    and returns token and user details. Uses the RegistrationSerializer.

    Methods:
        post(): Handles user registration and token creation.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        data = {}

        if serializer.is_valid():
            saved_account = serializer.save()
            token, _ = Token.objects.get_or_create(user=saved_account)
            data = {
                'token': token.key,
                'username': f"{saved_account.first_name} {saved_account.last_name}".strip(),
                'email': saved_account.email,
                'user_id': saved_account.id,
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = serializer.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class CustomLogInView(ObtainAuthToken):
    """
    API view for user login using token authentication.

    Authenticates user based on provided email and password.
    Returns token and user information on success.

    Methods:
        post(): Authenticates and logs in the user.
    """
    permission_classes= [AllowAny]
    serializer_class= UsernameAuthTokenSerializer  

    def post(self, request):
        serializer = self.serializer_class(
            data={
                'username': request.data.get('username'),
                'password': request.data.get('password')
            },
            context={'request': request}
        )

        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            username = f"{user.first_name} {user.last_name}".strip()
            data = {
                'token': token.key,
                'username': username,
                'email': user.email,
                'user_id': user.id,
    
            }
            return Response(data)
        else:
            return Response(
                {'error': 'Invalid username or password'},
                status=status.HTTP_400_BAD_REQUEST)
        
