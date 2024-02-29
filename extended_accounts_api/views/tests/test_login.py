from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse_lazy
from rest_framework.test import APITestCase, APIRequestFactory
from extended_accounts_api.helpers import LoginSerializer
from extended_accounts_api.views import LoginView
from extended_accounts_api.models import AccountModel as Account


class LoginViewTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.password = "testpassword"
        cls.factory = APIRequestFactory()
        cls.account = Account.objects.create_user(
            username="johndoe",
            password=cls.password,
            email="johndoe@mail.com",
            phone_number=123456789,
            is_active=True,
        )  ## To login an user it's to be active
        cls.url = reverse_lazy("extended_accounts_api:login")
        cls.data = {"username": cls.account.username, "password": cls.password}

    def test_view_setup(self):
        view = LoginView()
        self.assertEqual(view.serializer_class, LoginSerializer)
        self.assertEqual(view.http_method_names, ["post"])

    def test_login_OK_200(self):
        request = self.factory.post(self.url, self.data, format="json")
        middleware = SessionMiddleware(lambda get_response: None)
        middleware.process_request(request)
        request.session.save()
        response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.user, self.account)

    def test_login_wrong_password_KO_400(self):
        request = self.factory.post(
            self.url,
            data={"username": self.account.username, "password": "wrong_password"},
            format="json",
        )
        response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(request.user, AnonymousUser())

    def test_login_invalid_serializer_KO_400(self):
        request = self.factory.post(
            self.url,
            data={"username": self.account.username, "password": ""},
            format="json",
        )
        response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(request.user, AnonymousUser())
