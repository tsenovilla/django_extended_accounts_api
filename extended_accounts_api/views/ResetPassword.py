from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from extended_accounts_api.helpers import (
    ResetPasswordRequestSerializer,
    NewPasswordSerializer,
)
from extended_accounts_api.models import AccountModel as Account


class ResetPasswordRequestView(APIView):
    http_method_names = ["post"]

    def post(self, request):
        serializer = ResetPasswordRequestSerializer(data=request.data)
        if serializer.is_valid():
            account = list(serializer.validated_data.values())[
                0
            ]  ## If the serializer is valid, it returns the account.
            self.__send_reset_email(account)
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

    def __send_reset_email(self, account):
        subject = "Password Reset"
        message = f'Hello!\nWe have received your request to reset the account password, follow the link {self.request.build_absolute_uri(reverse_lazy("extended_accounts_api:reset_password", kwargs={"username": account.username, "token": default_token_generator.make_token(account)}))} to change your account password. If you did not request the change, you can ignore the message.'
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[account.email],
        )


class ResetPasswordView(UpdateAPIView):
    serializer_class = NewPasswordSerializer
    lookup_field = "username"
    http_method_names = ["put"]

    def get_queryset(self):
        return Account.objects.filter(username=self.kwargs["username"])

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def update(self, request, *args, **kwargs):
        account = self.get_object()
        if default_token_generator.check_token(account, kwargs["token"]):
            serializer = NewPasswordSerializer(account, data=request.data)
            if serializer.is_valid():
                serializer.save()
                login(request, account)
                return Response(status=status.HTTP_202_ACCEPTED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)
