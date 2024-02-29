from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from extended_accounts_api.models import AccountModel as Account


class AccountConfirmationView(APIView):
    http_method_names = ["get"]

    def get(self, request, **kwargs):
        ## If the user does not exist or their account is already validated, we return an error status code. We don't want this URL to be visited more than once per user. If everything is OK, we activate the user and log it in.
        try:
            account = Account.objects.get(username=kwargs["username"])
        except Account.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if account.is_active:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if default_token_generator.check_token(account, kwargs["token"]):
            account.update(is_active=True)
            login(request, account)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
