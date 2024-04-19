from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.urls import reverse_lazy
from django.conf import settings
from rest_framework.test import APITestCase, APIRequestFactory
from extended_accounts_api.helpers import NewPasswordSerializer
from extended_accounts_api.views import ResetPasswordRequestView, ResetPasswordView
from extended_accounts_api.models import AccountModel as Account


class ResetPasswordRequestViewTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.factory = APIRequestFactory()
        cls.account = Account.objects.create_user(
            username="johndoe",
            email="johndoe@mail.com",
            phone_number=123456789,
            is_active=True,
        )  ## To request a password reset, the user must be active
        cls.url = reverse_lazy("extended_accounts_api:reset_password_request")
        cls.data = {"email": cls.account.email}

    def test_view_setup(self):
        view = ResetPasswordRequestView
        self.assertTrue(view.http_method_names, ["post"])

    def test_reset_password_request_OK_202(self):
        request = self.factory.post(self.url, self.data, format="json")
        response = ResetPasswordRequestView.as_view()(request)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.subject, "Password Reset")
        self.assertIn(
            self.account.username, sent_mail.body
        )  ## Verifies that the email body contains the user's name (the content in the URL). We cannot verify the complete message because the token generated in the function is not necessarily the same as what we could generate here. In any case, this test is sufficient to ensure that the email was sent correctly.
        self.assertEqual(sent_mail.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertAlmostEqual(sent_mail.to, [self.account.email])

    def test_reset_password_request_no_valid_data_KO_404(self):
        request = self.factory.post(
            self.url, data={"email": "other_mail"}, format="json"
        )
        response = ResetPasswordRequestView.as_view()(request)
        self.assertEqual(response.status_code, 404)


class ResetPasswordViewTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.factory = APIRequestFactory()
        cls.account = Account.objects.create_user(
            username="johndoe", email="johndoe@mail.com", phone_number=123456789
        )
        cls.token = default_token_generator.make_token(cls.account)
        cls.url = reverse_lazy(
            "extended_accounts_api:reset_password",
            kwargs={"username": cls.account.username, "token": cls.token},
        )
        cls.data = {"password": "testpassword", "password_confirm": "testpassword"}

    def test_view_setup(self):
        view = ResetPasswordView()
        self.assertEqual(view.serializer_class, NewPasswordSerializer)
        self.assertEqual(view.lookup_field, "username")
        self.assertEqual(view.http_method_names, ["put"])
        view.kwargs = {"username": self.account.username}
        self.assertIn(self.account, view.get_queryset())
        self.assertEqual(len(view.get_queryset()), 1)

    def test_reset_password_OK_202(self):
        request = self.factory.put(self.url, self.data, format="json")
        middleware = SessionMiddleware(lambda get_response: None)
        middleware.process_request(request)
        request.session.save()
        response = ResetPasswordView.as_view()(
            request, username=self.account.username, token=self.token
        )
        self.assertEqual(response.status_code, 202)
        self.account.refresh_from_db()
        self.assertTrue(self.account.check_password(self.data["password"]))

    def test_reset_password_user_not_found_KO_404(self):
        request = self.factory.put(
            reverse_lazy(
                "extended_accounts_api:reset_password",
                kwargs={"username": "other_user", "token": "doesntmatter"},
            ),
            self.data,
            format="json",
        )
        response = ResetPasswordView.as_view()(
            request, username="other_user", token="doesntmatter"
        )
        self.assertEqual(response.status_code, 404)

    def test_reset_password_wrong_token_KO_400(self):
        request = self.factory.put(
            reverse_lazy(
                "extended_accounts_api:reset_password",
                kwargs={"username": self.account.username, "token": "wrongtoken"},
            ),
            self.data,
            format="json",
        )
        response = ResetPasswordView.as_view()(
            request, username=self.account.username, token="wrong_token"
        )
        self.assertEqual(response.status_code, 400)

    def test_reset_password_invalid_data_KO_400(self):
        request = self.factory.put(self.url, {}, format="json")
        response = ResetPasswordView.as_view()(
            request, username=self.account.username, token=self.token
        )
        self.assertEqual(response.status_code, 400)
