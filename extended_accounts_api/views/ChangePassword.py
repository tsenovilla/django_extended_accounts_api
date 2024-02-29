from django.contrib.auth import update_session_auth_hash
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from extended_accounts_api.helpers import NewPasswordSerializer, IsSelf
from extended_accounts_api.models import AccountModel as Account


class ChangePasswordView(UpdateAPIView):
    serializer_class = NewPasswordSerializer
    lookup_field = "username"
    permission_classes = [IsSelf]
    http_method_names = ["put"]

    def get_queryset(self):
        return Account.objects.filter(username=self.kwargs["username"])

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def update(self, request, *args, **kwargs):
        account = self.get_object()
        serializer = NewPasswordSerializer(account, data=request.data)
        if serializer.is_valid():
            serializer.save()
            update_session_auth_hash(request, account)
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
