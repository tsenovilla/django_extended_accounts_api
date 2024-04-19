from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from rest_framework.test import APITestCase, override_settings
from extended_accounts_api.helpers import AccountSerializer
from extended_accounts_api.models import AccountModel as Account
from PIL import Image
from io import BytesIO
import tempfile, shutil, os

MEDIA_ROOT = tempfile.mkdtemp()


def create_test_image():
    image_buffer = BytesIO()
    image_object = Image.new("RGB", (1, 1))
    image_object.save(image_buffer, "png")
    image_buffer.seek(0)
    image = SimpleUploadedFile(
        "test_image.png",
        image_buffer.read(),
    )
    return image


## We have to use MultiPartParser to test the image upload trough the serializer. In the real app this is done in the ViewSet using the serializer, but these tests use the default setting
REST_FRAMEWORK = settings.REST_FRAMEWORK.copy()
REST_FRAMEWORK.update(
    {
        "DEFAULT_PARSER_CLASSES": [
            "rest_framework.parsers.MultiPartParser",
            "rest_framework.parsers.JSONParser",
        ]
    }
)


@override_settings(MEDIA_ROOT=MEDIA_ROOT, REST_FRAMEWORK=REST_FRAMEWORK)
class AccountSerializerTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.account = Account.objects.create_user(
            username="johndoe",
            email="johndoe@mail.com",
            phone_number=123456789,
            profile_image=create_test_image(),
        )  ## This is the created account to play with
        Account.objects.create_user(
            username="mattdoe", email="mattdoe@mail.com", phone_number=987654321
        )  ## Just another account to test integrity
        cls.data = {  ## A piece of data to pass to serializers
            "username": "jdoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "jdoe@mail.com",
            "phone_number": 123123123,
            "password": {
                "password": "testpassword",
                "password_confirm": "testpassword",
            },
        }

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass(*args, **kwargs)

    def __add_image_to_data(self):
        data = self.data.copy()
        data.update(
            {"profile_image": create_test_image()}
        )  ## The used image has to be passed to each test  that needs it individually, otherwise it's consumed by the first test using it and the following ones will fail due to an empty file erro
        return data

    def __modify_data(self, to_modify):
        data = self.data.copy()
        data.update(to_modify)
        return data

    def __pop_data(self, key):
        data = self.data.copy()
        data.pop(key)
        return data

    def test_account_serializer_create(self):
        data = self.__add_image_to_data()
        serializer = AccountSerializer(data=data)
        serializer.is_valid()
        account = serializer.create(serializer.validated_data)
        self.assertEqual(account.username, self.data["username"])
        self.assertEqual(account.email, self.data["email"])
        self.assertTrue(account.check_password(self.data["password"]["password"]))
        self.assertEqual(account.profile.first_name, self.data["first_name"])
        self.assertEqual(account.profile.last_name, self.data["last_name"])
        self.assertEqual(account.profile.phone_number, self.data["phone_number"])
        self.assertIn(
            account.profile.profile_image.name + ".png", os.listdir(MEDIA_ROOT)
        )
        self.assertIn(
            account.profile.profile_image.name + ".webp", os.listdir(MEDIA_ROOT)
        )

    def test_account_serializer_update(self):
        data = self.__add_image_to_data()
        serializer = AccountSerializer(self.account, data=data)
        serializer.is_valid()
        previous_image_name = self.account.profile.profile_image.name
        self.assertIn(previous_image_name + ".png", os.listdir(MEDIA_ROOT))
        self.assertIn(previous_image_name + ".webp", os.listdir(MEDIA_ROOT))
        account = serializer.update(self.account, serializer.validated_data)
        self.assertEqual(account.username, self.data["username"])
        self.assertEqual(account.email, self.data["email"])
        self.assertEqual(account.profile.first_name, self.data["first_name"])
        self.assertEqual(account.profile.last_name, self.data["last_name"])
        self.assertEqual(account.profile.phone_number, self.data["phone_number"])
        self.assertIn(
            account.profile.profile_image.name + ".png", os.listdir(MEDIA_ROOT)
        )
        self.assertIn(
            account.profile.profile_image.name + ".webp", os.listdir(MEDIA_ROOT)
        )
        self.assertNotIn(previous_image_name + ".png", os.listdir(MEDIA_ROOT))
        self.assertNotIn(previous_image_name + ".webp", os.listdir(MEDIA_ROOT))

    def test_account_serializer_init(self):
        put_context = {"request": type("Request", (object,), {"method": "PUT"})}
        serializer_put = AccountSerializer(context=put_context)
        self.assertNotIn("password", serializer_put.fields.keys())

        patch_context = {"request": type("Request", (object,), {"method": "PATCH"})}
        serializer_patch = AccountSerializer(context=patch_context)
        self.assertNotIn("password", serializer_patch.fields.keys())

    def test_account_serializer_to_representation(self):
        serializer = AccountSerializer()
        representation = serializer.to_representation(self.account)
        self.assertIn("username", representation.keys())
        self.assertIn("first_name", representation.keys())
        self.assertIn("last_name", representation.keys())
        self.assertIn("email", representation.keys())
        self.assertIn("phone_number", representation.keys())
        self.assertIn("profile_image", representation.keys())
        self.assertIn("date_joined", representation.keys())

    ## TEST VALIDATORS

    def test_account_serializer_OK(self):
        serializer = AccountSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())

    def test_account_serializer_retains_username_OK(self):
        data = self.__modify_data({"username": "johndoe"})
        serializer = AccountSerializer(self.account, data=data)
        self.assertTrue(serializer.is_valid())

    def test_account_serializer_retains_email_OK(self):
        data = self.__modify_data({"email": "johndoe@mail.com"})
        serializer = AccountSerializer(self.account, data=data)
        self.assertTrue(serializer.is_valid())

    def test_account_serializer_retains_phone_number_OK(self):
        data = self.__modify_data({"phone_number": 123456789})
        serializer = AccountSerializer(self.account, data=data)
        self.assertTrue(serializer.is_valid())

    def test_account_serializer_without_username_KO(self):
        data = self.__pop_data("username")
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_without_first_name_KO(self):
        data = self.__pop_data("first_name")
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_without_last_name_KO(self):
        data = self.__pop_data("last_name")
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_without_email_KO(self):
        data = self.__pop_data("email")
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_without_phone_number_KO(self):
        data = self.__pop_data("phone_number")
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_without_password_KO(self):
        data = self.__pop_data("password")
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_repeated_username_KO(self):
        data = self.__modify_data({"username": "johndoe"})
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_repeated_email_KO(self):
        data = self.__modify_data({"email": "johndoe@mail.com"})
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_repeated_phone_number_KO(self):
        data = self.__modify_data({"phone_number": 123456789})
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_registered_account_uses_already_registered_username_KO(
        self,
    ):
        data = self.__modify_data({"username": "mattdoe"})
        serializer = AccountSerializer(self.account, data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_registered_account_uses_already_registered_email_KO(
        self,
    ):
        data = self.__modify_data({"email": "mattdoe@mail.com"})
        serializer = AccountSerializer(self.account, data=data)
        self.assertFalse(serializer.is_valid())

    def test_account_serializer_registered_account_uses_already_registered_phone_KO(
        self,
    ):
        data = self.__modify_data({"phone_number": 987654321})
        serializer = AccountSerializer(self.account, data=data)
        self.assertFalse(serializer.is_valid())
