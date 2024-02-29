from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from rest_framework.test import (
    APITestCase,
    APIRequestFactory,
    override_settings,
    force_authenticate,
)
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from extended_accounts_api.helpers import AccountSerializer, IsSelf
from extended_accounts_api.models import AccountModel as Account
from extended_accounts_api.views import AccountsViewSet
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


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AccountsViewSetTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.factory = APIRequestFactory()
        cls.account = Account.objects.create_user(
            username="johndoe",
            email="johndoe@mail.com",
            phone_number=123456789,
            profile_image=create_test_image(),
        )
        cls.data = {
            "username": "jdoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "jdoe@mail.com",
            "phone_number": 987654321,
            "password.password": "testpassword",  ## As we're sending multipart data, we have to accomplish with a form request due to multipart parser doesn't support nested data. But writing the NewPasswordSerializer in this way does the trick
            "password.password_confirm": "testpassword",
        }
        cls.url = "extended_accounts_api/"

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

    def test_view_setup(self):
        view = AccountsViewSet()
        self.assertEqual(view.serializer_class, AccountSerializer)
        self.assertEqual(view.lookup_field, "username")
        self.assertEqual(view.parser_classes, [MultiPartParser, JSONParser])
        view.kwargs = {"username": self.account.username}
        self.assertIn(self.account, view.get_queryset())
        self.assertEqual(len(view.get_queryset()), 1)
        ## Permissions depending on the action
        view.action = "list"
        self.assertIsInstance(view.get_permissions()[0], IsAuthenticated)
        view.action = "retrieve"
        self.assertIsInstance(view.get_permissions()[0], IsAuthenticated)
        view.action = "update"
        self.assertIsInstance(view.get_permissions()[0], IsSelf)
        view.action = "partial_update"
        self.assertIsInstance(view.get_permissions()[0], IsSelf)
        view.action = "destroy"
        self.assertIsInstance(view.get_permissions()[0], IsSelf)
        view.action = "delete_profile_image"
        self.assertIsInstance(view.get_permissions()[0], IsSelf)
        view.action = "create"
        self.assertEqual(view.get_permissions(), [])

    def test_create_account_OK_201(self):
        data = self.__add_image_to_data()
        request = self.factory.post(self.url, data)
        response = AccountsViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)

        account = Account.objects.get(username=self.data["username"])
        self.assertEqual(account.username, self.data["username"])
        self.assertEqual(account.email, self.data["email"])
        self.assertEqual(account.profile.first_name, self.data["first_name"])
        self.assertEqual(account.profile.last_name, self.data["last_name"])
        self.assertFalse(
            account.is_active
        )  ## Upon creation, the user isn't active until they confirm their account
        self.assertEqual(
            account.profile.phone_number, self.data["phone_number"]
        )  ## The phone has been registered correctly in the profile
        ## The image's been uploaded
        self.assertIn(
            account.profile.profile_image.name + ".png", os.listdir(MEDIA_ROOT)
        )
        self.assertIn(
            account.profile.profile_image.name + ".webp", os.listdir(MEDIA_ROOT)
        )
        ## To check the password, the account must be active
        account.update(is_active=True)
        self.assertTrue(account.check_password(self.data["password.password"]))

        ## Check that the email was correctly sent
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.subject, "Account Confirmation")
        self.assertIn(
            self.data["username"], sent_mail.body
        )  ## Verify that the email body contains the user's name (the content in the URL). We cannot verify the complete message because the token generated in the function may not necessarily be the same as what we could generate here. In any case, this test is sufficient to see that the email was sent correctly
        self.assertEqual(
            sent_mail.from_email,
            settings.DEFAULT_FROM_EMAIL,
        )
        self.assertAlmostEqual(sent_mail.to, [self.data["email"]])

    def test_create_account_invalid_data_KO_400(self):
        request = self.factory.post(self.url, {}, format="json")
        response = AccountsViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400)

    def test_update_account_OK(self):
        previous_image_name = self.account.profile.profile_image.name
        self.assertIn(previous_image_name + ".png", os.listdir(MEDIA_ROOT))
        self.assertIn(previous_image_name + ".webp", os.listdir(MEDIA_ROOT))
        data = self.__add_image_to_data()
        data.pop("password.password")  ## Put don't have password
        data.pop("password.password_confirm")
        request = self.factory.put(self.url + "/" + self.account.username, data)
        force_authenticate(request, self.account)
        response = AccountsViewSet.as_view({"put": "update"})(
            request, username=self.account.username
        )
        self.assertEqual(response.status_code, 200)
        account = Account.objects.get(
            pk=self.account.pk
        )  ## It's better to get instead of refreshing from the db, as self.account is a crossed object throughout the TestCase and refreshing it here may contaminate other tests
        self.assertEqual(
            account.username, self.data["username"]
        )  ## Check that the information has been updated by checking one of the fields
        ## The images are well updated
        self.assertIn(
            account.profile.profile_image.name + ".png", os.listdir(MEDIA_ROOT)
        )
        self.assertIn(
            account.profile.profile_image.name + ".webp", os.listdir(MEDIA_ROOT)
        )
        self.assertNotIn(previous_image_name + ".png", os.listdir(MEDIA_ROOT))
        self.assertNotIn(previous_image_name + ".webp", os.listdir(MEDIA_ROOT))

    def test_partial_update_account_OK(self):
        data = self.data.copy()
        ## Remove some fields from the request data
        data.pop("first_name")
        data.pop("phone_number")
        data.pop("password.password")
        data.pop("password.password_confirm")
        request = self.factory.patch(
            self.url + "/" + self.account.username, data, format="json"
        )
        force_authenticate(request, self.account)
        response = AccountsViewSet.as_view({"patch": "partial_update"})(
            request, username=self.account.username
        )
        self.assertEqual(response.status_code, 200)
        account = Account.objects.get(pk=self.account.pk)
        self.assertEqual(
            account.username, self.data["username"]
        )  ## Check that the information has been updated by checking one of the fields


## We separate the tests of destroy request and destroy_profile_image request as if it's called before the update test in the previous TestCase, as it would interact with the MEDIA_ROOT and contaminate the test environment


class AccountsViewSetDestroyAccountTestCase(APITestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.factory = APIRequestFactory()
        cls.account = Account.objects.create_user(
            username="johndoe", email="johndoe@mail.com", phone_number=123456789
        )
        cls.url = "extended_accounts_api/"

    def test_destroy_account_OK(self):
        request = self.factory.delete(self.url + "/" + self.account.username)
        force_authenticate(request, self.account)
        response = AccountsViewSet.as_view({"delete": "destroy"})(
            request, username=self.account.username
        )
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(Account.DoesNotExist):
            Account.objects.get(username=self.account.username)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AccountsViewSetDeleteProfileImageTestCase(APITestCase):
    def setUp(
        self,
    ):  ## Each test needs its own image, then setUp's more suitable than setUpClass
        self.factory = APIRequestFactory()
        self.account = Account.objects.create_user(
            username="johndoe",
            email="johndoe@mail.com",
            phone_number=123456789,
            profile_image=create_test_image(),
        )
        self.url = f"extended_accounts_api/{self.account.username}/delete_profile_image"

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass(*args, **kwargs)

    def __make_request(self):
        request = self.factory.delete(self.url)
        force_authenticate(request, self.account)
        response = AccountsViewSet.as_view({"delete": "delete_profile_image"})(
            request, username=self.account.username
        )
        return response

    def test_delete_profile_image_OK_204(self):
        image_name = self.account.profile.profile_image.name
        self.assertIn(image_name + ".png", os.listdir(MEDIA_ROOT))
        self.assertIn(image_name + ".webp", os.listdir(MEDIA_ROOT))
        response = self.__make_request()
        self.assertEqual(response.status_code, 204)
        self.assertNotIn(image_name + ".png", os.listdir(MEDIA_ROOT))
        self.assertNotIn(image_name + ".webp", os.listdir(MEDIA_ROOT))

    def test_delete_profile_image_KO_400(self):
        self.account.update(profile_image=None)
        response = self.__make_request()
        self.assertEqual(response.status_code, 400)
