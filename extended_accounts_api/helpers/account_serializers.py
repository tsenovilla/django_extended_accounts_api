from django.core.validators import RegexValidator
from rest_framework import serializers
from extended_accounts_api.models import AccountModel as Account
from .password_serializers import NewPasswordSerializer


class AccountSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.IntegerField(
        required=True,
        validators=[
            RegexValidator(
                regex=r"^[0-9]{9}$",
                message="Phone number must contain 9 digits",  ## This validation is due to spanish phone numbers are composed by 9 digits, adapt it accordingly with your needs
            )
        ],
    )
    profile_image = serializers.ImageField(required=False)
    password = NewPasswordSerializer(required=True, write_only=True)

    class Meta:
        model = Account
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "profile_image",
            "password",
        ]

    def __init__(self, *args, **kwargs):
        try:  ## In PUT and PATCH, context is available, and we can properly filter so that passwords are not required (those are updated through their own view)
            if kwargs["context"]["request"].method in ["PUT", "PATCH"]:
                self.fields.pop("password")
        except:
            pass
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        password = validated_data.pop("password")
        password_serializer = NewPasswordSerializer(data=password)
        password_serializer.is_valid(raise_exception=True)
        validated_data["password"] = password_serializer.validated_data["password"]
        return Account.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        instance.update(**validated_data)
        return instance

    def to_representation(
        self, instance
    ):  ## As the profile information comes from a related model, we have to overwrite how the serializer is represented
        return {
            "username": instance.username,
            "first_name": instance.profile.first_name,
            "last_name": instance.profile.last_name,
            "email": instance.email,
            "phone_number": instance.profile.phone_number,
            "profile_image": instance.profile.profile_image.name,
        }

    def validate_username(self, value):
        try:
            instance_pk = self.instance.pk
        except (
            AttributeError
        ):  ## If the instance is not defined, the object is newly created
            if Account.objects.all().filter(username=value):
                raise serializers.ValidationError(
                    "The username entered is already registered by another user"
                )
        else:
            if Account.objects.exclude(pk=instance_pk).filter(username=value):
                raise serializers.ValidationError(
                    "The username entered is already registered by another user"
                )
        return value

    def validate_email(self, value):
        try:
            instance_pk = self.instance.pk
        except (
            AttributeError
        ):  ## If the instance is not defined, the object is newly created
            if Account.objects.all().filter(email=value):
                raise serializers.ValidationError(
                    "The email entered is already registered by another user"
                )
        else:
            if Account.objects.exclude(pk=instance_pk).filter(email=value):
                raise serializers.ValidationError(
                    "The email entered is already registered by another user"
                )
        return value

    def validate_phone_number(self, value):
        try:
            instance_pk = self.instance.pk
        except AttributeError:
            if Account.objects.all().filter(profile__phone_number=value):
                raise serializers.ValidationError(
                    "The entered phone number is already registered"
                )
        else:
            if Account.objects.exclude(pk=instance_pk).filter(
                profile__phone_number=value
            ):
                raise serializers.ValidationError(
                    "The entered phone number is already registered"
                )
        return value
