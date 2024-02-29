from django.urls import path, include
from rest_framework.routers import DefaultRouter
from extended_accounts_api.views import (
    AccountsViewSet,
    LoginView,
    LogoutView,
    ResetPasswordRequestView,
    ResetPasswordView,
    ChangePasswordView,
    AccountConfirmationView,
)


router = DefaultRouter()
router.register(r"", AccountsViewSet, basename="extended_accounts_api")


app_name = "extended_accounts_api"
urlpatterns = [
    path(
        "account_confirmation/<str:username>/<token>/",
        AccountConfirmationView.as_view(),
        name="account_confirmation",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "reset_password_request/",
        ResetPasswordRequestView.as_view(),
        name="reset_password_request",
    ),
    path(
        "reset_password/<str:username>/<token>/",
        ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path(
        "change_password/<str:username>",
        ChangePasswordView.as_view(),
        name="change_password",
    ),
]

urlpatterns += [path("", include(router.urls))]
