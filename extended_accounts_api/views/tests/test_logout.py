from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse_lazy
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from extended_accounts_api.views import LogoutView
from extended_accounts_api.models import AccountModel as Account


class LogoutViewTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.factory = APIRequestFactory()
        cls.account = Account.objects.create_user(
            username="johndoe",
            password="testpassword",
            email="johndoe@mail.com",
            phone_number=123456789,
        )
        cls.url = reverse_lazy("extended_accounts_api:logout")

    def test_view_setup(self):
        view = LogoutView()
        self.assertEqual(view.http_method_names, ["post"])

    def test_logout_OK_200(self):
        request = self.factory.post(self.url)
        middleware = SessionMiddleware(lambda get_response: None)
        middleware.process_request(request)
        request.session.save()
        force_authenticate(request, self.account)
        response = LogoutView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.user, AnonymousUser())
