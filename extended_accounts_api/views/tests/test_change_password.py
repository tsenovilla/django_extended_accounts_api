from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse_lazy
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from extended_accounts_api.helpers import NewPasswordSerializer, IsSelf
from extended_accounts_api.views import ChangePasswordView
from extended_accounts_api.models import AccountModel as Account


class ChangePasswordViewTestCase(APITestCase):
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
        cls.url = reverse_lazy(
            "extended_accounts_api:change_password",
            kwargs={"username": cls.account.username},
        )
        cls.data = {"password": "testpassword2", "password_confirm": "testpassword2"}

    def test_view_setup(self):
        view = ChangePasswordView()
        self.assertEqual(view.serializer_class, NewPasswordSerializer)
        self.assertEqual(view.lookup_field, "username")
        self.assertEqual(view.permission_classes, [IsSelf])
        self.assertEqual(view.http_method_names, ["put"])
        view.kwargs = {"username": self.account.username}
        self.assertIn(self.account, view.get_queryset())
        self.assertEqual(len(view.get_queryset()), 1)

    def test_change_password_OK_202(self):
        request = self.factory.put(self.url, self.data, format="json")
        force_authenticate(request, user=self.account)
        middleware = SessionMiddleware(lambda get_response: None)
        middleware.process_request(request)
        request.session.save()
        response = ChangePasswordView.as_view()(request, username=self.account.username)
        self.assertEqual(response.status_code, 202)
        self.account.refresh_from_db()
        self.assertTrue(self.account.check_password("testpassword2"))

    def test_invalid_serializer_400(self):
        request = self.factory.put(self.url, {}, format="json")
        force_authenticate(request, user=self.account)
        response = ChangePasswordView.as_view()(request, username=self.account.username)
        self.assertEqual(response.status_code, 400)

    def test_unauthorized_access_403(self):
        Account.objects.create_user(
            username="other_user", email="other@mail.com", phone_number=987654321
        )
        request = self.factory.put(
            reverse_lazy(
                "extended_accounts_api:change_password",
                kwargs={"username": "other_user"},
            ),
            self.data,
            format="json",
        )
        force_authenticate(request, user=self.account)
        response = ChangePasswordView.as_view()(request, username="other_user")
        self.assertEqual(response.status_code, 403)
