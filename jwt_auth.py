from django.shortcuts import render
from rest_framework.request import Request

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from .models import CustomUser
from django.db.transaction import atomic
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken

class HelloView(APIView):
    permission_classes = (IsAuthenticated, )
  
    def get(self, request):
        content = {'message': 'Hello, Chicmic'}
        return Response(content)

class Signup(ModelViewSet):
    queryset         = CustomUser.objects
    serializer_class = None
    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            username     = data.get('username')
            password     = data.get('password')
            email        = data.get('email')
            photo        = request.FILES.get('image')
            phone_number = data.get('phone_number')
            age          = data.get('age')
            gender       = data.get('gender')
            if self.queryset.filter(email = email).exists():
                    return Response({
                        "message" : "Email already exists",
                        "status" : False,
                        "response": "fail"},status.HTTP_409_CONFLICT)
            with atomic():
                user = self.queryset.create(
                    username     = username,
                    email        = email,
                    photo        = photo,
                    phone_number = phone_number,
                    age          = age,
                    gender       = gender
                )
                user.set_password(password)
                user.verified = True
                user.save()
                return Response({
                        "message":"User registation completed successfully",
                        "status": True,
                        "response": "success", }, status=status.HTTP_201_CREATED)

        except Exception as error:
           return Response({
                        "message":str(error),
                        "status": False,
                        "response": "fail", }, status=status.HTTP_400_BAD_REQUEST)


class CustomJWTObtainPair(TokenObtainPairView):
    """
    CustomJWTObtainPair Class:

    This class extends TokenObtainPairView from Django Rest Framework SimpleJWT. It handles user authentication
    by validating login credentials (email or username and password) provided in a POST request. If valid, it
    generates and returns JSON Web Tokens (JWT) for the authenticated user.

    Attributes:
        Inherits TokenObtainPairView, which provides token generation functionality.

    Methods:
        - post(self, request, *args, **kwargs):
            Handles POST requests for obtaining JWT tokens.
            - Extracts 'loginid' and 'password' from request data.
            - Retrieves the user based on 'loginid' (email or username).
            - Checks if the provided password matches the user's stored password.
            - Generates refresh and access tokens if authentication is successful.
            - Returns appropriate success or error response.

    Usage:
        Create an instance of CustomJWTObtainPair class to handle authentication requests.
        Call the 'post' method with a POST request containing 'loginid' and 'password' in the request data.

    Example:
        custom_authenticator = CustomJWTObtainPair.as_view()
        For usage in a Django URL pattern, refer to Django Rest Framework documentation.
"""

    def post(self, request, *args, **kwargs):
        try:
            # Get the 'loginid' and 'password' from the request data
            loginid = request.data.get('loginid')
            password = request.data.get('password')

            # Get the user based on 'email' or 'username'
            user = CustomUser.objects.get(Q(email=loginid) | Q(username=loginid))

            # Check if the provided password matches the user's password
            password_matches = check_password(password, user.password)
            if password_matches:
                # Get the refresh token for the user
                refresh_token_data = get_refresh_token_for_user(user)

                # If refresh token found, return success response with tokens
                if refresh_token_data:
                    return Response({
                        "data": refresh_token_data,
                        "status": True,
                        "response": "success"
                    }, status.HTTP_200_OK)

        except Exception as error:
            # If any exception occurs, return error response
            return Response({
                "message": str(error),
                "status": False,
                "response": "fail"
            }, status.HTTP_400_BAD_REQUEST)



def get_refresh_token_for_user(user):
   """
    Obtain Refresh and Access Tokens for a User.

    This method retrieves a pair of tokens (Refresh Token and Access Token)
    for the specified user using Django Rest Framework SimpleJWT's
    `RefreshToken.for_user` method.

    Parameters:
        user (User object): The user for whom the tokens are requested.

    Returns:
        dict: A dictionary with "refresh" and "access_token" keys containing
              the Refresh Token and Access Token as strings.
    """
   refresh_tokens = RefreshToken.for_user(user)
   
   return {
        "refresh": str(refresh_tokens),
        "access_token": str(refresh_tokens.access_token)
    }


