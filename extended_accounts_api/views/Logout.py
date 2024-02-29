from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class LogoutView(APIView):
    http_method_names = ["post"]

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)
