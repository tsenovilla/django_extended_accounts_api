from django.urls import path, include
from django_extended_accounts_api.get_csrf_token import get_csrf_token

urlpatterns = []

## If you are using the extended_accounts_api app
urlpatterns += [
    path(
        "extended_accounts_api/",
        include("extended_accounts_api.urls", namespace="extended_accounts_api"),
    ),
    path(
        "get_csrf_token/", get_csrf_token
    ),  ## Use this endpoint to provide your front-end with a valid csrf token.
]
