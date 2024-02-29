from rest_framework.test import APITestCase, APIRequestFactory
from extended_accounts_api.helpers import IsSelf
from extended_accounts_api.models import AccountModel as Account


class IsSelfTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.johndoe = Account.objects.create_user(
            username="johndoe", email="johndoe@mail.com", phone_number=123456789
        )
        cls.mattdoe = Account.objects.create_user(
            username="mattdoe", email="mattdoe@mail.com", phone_number=987654321
        )
        factory = APIRequestFactory()
        cls.request = factory.get("/")
        cls.request.user = cls.johndoe
        cls.permission = IsSelf()

    def test_has_object_permission_self_OK(self):
        self.assertTrue(
            self.permission.has_object_permission(self.request, None, self.johndoe)
        )

    def test_has_object_permission_other_user_KO(self):
        self.assertFalse(
            self.permission.has_object_permission(self.request, None, self.mattdoe)
        )
