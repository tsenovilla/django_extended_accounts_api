from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from extended_accounts_api.helpers import LoginSerializer


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    http_method_names = ["post"]

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            account = authenticate(
                request,
                username=request.data["username"],
                password=request.data["password"],
            )
            if account:
                login(request, account)
                return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
