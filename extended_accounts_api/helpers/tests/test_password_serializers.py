from rest_framework.test import APITestCase
from extended_accounts_api.helpers import (
    ResetPasswordRequestSerializer,
    NewPasswordSerializer,
)
from extended_accounts_api.models import AccountModel as Account


class ResetPasswordRequestSerializerTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.account = Account.objects.create_user(
            username="johndoe",
            email="johndoe@mail.com",
            phone_number=123456789,
            is_active=True,
        )  ## The user must be active to request a password reset

    def test_reset_password_request_serializer_OK(self):
        serializer = ResetPasswordRequestSerializer(data={"email": "johndoe@mail.com"})
        self.assertTrue(serializer.is_valid())

    def test_reset_password_request_serializer_no_email_KO(self):
        serializer = ResetPasswordRequestSerializer(data={})
        self.assertFalse(serializer.is_valid())

    def test_reset_password_request_serializer_unregistered_email_KO(self):
        serializer = ResetPasswordRequestSerializer(data={"email": "jdoe@mail.com"})
        self.assertFalse(serializer.is_valid())

    def test_reset_password_request_serializer_account_not_active_KO(self):
        Account.objects.create_user(
            username="jdoe", email="jdoe@mail.com", phone_number=987654321
        )
        serializer = ResetPasswordRequestSerializer(data={"email": "jdoe@mail.com"})
        self.assertFalse(serializer.is_valid())


class NewPasswordSerializerTests(APITestCase):
    def test_new_password_serializer_update(self):
        account = Account.objects.create_user(
            username="johndoe",
            password="testpassword",
            email="johndoe@mail.com",
            phone_number=123456789,
        )
        serializer = NewPasswordSerializer(
            account,
            data={"password": "testpassword2", "password_confirm": "testpassword2"},
        )
        self.assertTrue(account.check_password("testpassword"))
        serializer_valid = serializer.is_valid()
        self.assertTrue(serializer_valid)
        serializer.update(account, serializer.validated_data)
        self.assertTrue(account.check_password("testpassword2"))

    ## VALIDATORS TESTS
    def test_new_password_serializer_OK(self):
        serializer = NewPasswordSerializer(
            data={"password": "testpassword", "password_confirm": "testpassword"}
        )
        self.assertTrue(serializer.is_valid())

    def test_new_password_serializer_no_password_KO(self):
        serializer = NewPasswordSerializer(data={"password_confirm": "testpassword"})
        self.assertFalse(serializer.is_valid())

    def test_new_password_serializer_no_password_confirm_KO(self):
        serializer = NewPasswordSerializer(data={"password": "testpassword"})
        self.assertFalse(serializer.is_valid())

    def test_new_password_serializer_different_passwords_KO(self):
        serializer = NewPasswordSerializer(
            data={"password": "testpassword", "password_confirm": "passwordtest"}
        )
        self.assertFalse(serializer.is_valid())
