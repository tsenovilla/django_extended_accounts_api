from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.decorators import action
from extended_accounts_api.helpers import AccountSerializer, IsSelf
from extended_accounts_api.models import AccountModel as Account


class AccountsViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    lookup_field = "username"
    parser_classes = [MultiPartParser, JSONParser]

    def get_permissions(self):
        IsAuthenticated_methods = ["list", "retrieve", "get_authenticated_account"]
        IsSelf_methods = [
            "update",
            "partial_update",
            "destroy",
            "delete_profile_image",
        ]
        if self.action in IsAuthenticated_methods:
            permission_classes = [IsAuthenticated]
        elif self.action in IsSelf_methods:
            permission_classes = [IsSelf]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    @method_decorator(csrf_protect)
    def create(self, request, *args, **kwargs):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save()
            self.__send_confirmation_email(account)
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    ## Unsafe methods [POST, PUT, PATCH, DELETE] require CSRF with SessionAuthentication.
    @method_decorator(csrf_protect)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    @action(detail=True, methods=["delete"], url_path="delete_profile_image")
    def delete_profile_image(self, request, username):
        account = self.get_object()
        if account.profile.profile_image:
            account.update(profile_image=None)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, url_path="get_authenticated_account")
    def get_authenticated_account(self, request):
        return Response(
            AccountSerializer().to_representation(
                instance=Account.objects.get(username=request.user.username)
            ),
            status=status.HTTP_200_OK,
        )

    def __send_confirmation_email(self, account):
        subject = "Account Confirmation"
        message = f'Hello!\nWe have received your request to create an account, follow the link {self.request.build_absolute_uri(reverse_lazy("extended_accounts_api:account_confirmation", kwargs={"username": account.username, "token": default_token_generator.make_token(account)}))} to confirm your account. The link will be valid for 15 minutes, if you do not confirm the account within that time frame you will have to start the process again. If you did not request this account, you can ignore this message.'
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[account.email],
        )
