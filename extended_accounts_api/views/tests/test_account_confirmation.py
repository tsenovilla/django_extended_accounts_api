from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse_lazy
from rest_framework.test import APITestCase, APIRequestFactory
from extended_accounts_api.views import AccountConfirmationView
from extended_accounts_api.models import AccountModel as Account


class AccountConfirmationViewTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.factory = APIRequestFactory()
        cls.account = Account.objects.create_user(
            username="johndoe", email="johndoe@mail.com", phone_number=123456789
        )
        cls.token = default_token_generator.make_token(cls.account)

    def test_view_setup(self):
        view = AccountConfirmationView()
        self.assertEqual(view.http_method_names, ["get"])

    def test_ok(self):
        request = self.factory.get(
            reverse_lazy(
                "extended_accounts_api:account_confirmation",
                kwargs={
                    "username": self.account.username,
                    "token": self.token,
                },
            )
        )
        middleware = SessionMiddleware(lambda get_response: None)
        middleware.process_request(request)
        request.session.save()
        response = AccountConfirmationView.as_view()(
            request, username=self.account.username, token=self.token
        )
        self.assertEqual(200, response.status_code)
        self.account.refresh_from_db()
        self.assertTrue(self.account.is_active)

    def test_user_not_found_404(self):
        request = self.factory.get(
            reverse_lazy(
                "extended_accounts_api:account_confirmation",
                kwargs={"username": "jdoe", "token": "doesntmatter"},
            )
        )
        response = AccountConfirmationView.as_view()(
            request, username="jdoe", token="doesntmatter"
        )
        self.assertEqual(404, response.status_code)

    def test_active_user_400(self):
        self.account.update(is_active=True)
        request = self.factory.get(
            reverse_lazy(
                "extended_accounts_api:account_confirmation",
                kwargs={
                    "username": self.account.username,
                    "token": self.token,
                },
            )
        )
        response = AccountConfirmationView.as_view()(
            request, username=self.account.username, token=self.token
        )
        self.assertEqual(400, response.status_code)

    def test_incorrect_token_400(self):
        request = self.factory.get(
            reverse_lazy(
                "extended_accounts_api:account_confirmation",
                kwargs={"username": self.account.username, "token": "wrong_token"},
            )
        )
        response = AccountConfirmationView.as_view()(
            request, username=self.account.username, token="wrong_token"
        )
        self.assertEqual(400, response.status_code)
