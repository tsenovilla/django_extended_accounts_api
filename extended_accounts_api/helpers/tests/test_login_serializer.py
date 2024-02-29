from rest_framework.test import APITestCase
from extended_accounts_api.helpers import LoginSerializer


class LoginSerializerTestCase(APITestCase):
    def test_login_serializer_OK(self):
        serializer = LoginSerializer(
            data={"username": "johndoe", "password": "testpassword"}
        )
        self.assertTrue(serializer.is_valid())

    def test_login_serializer_no_username_KO(self):
        serializer = LoginSerializer(data={"password": "testpassword"})
        self.assertFalse(serializer.is_valid())

    def test_login_serializer_no_password_KO(self):
        serializer = LoginSerializer(data={"username": "johndoe"})
        self.assertFalse(serializer.is_valid())
