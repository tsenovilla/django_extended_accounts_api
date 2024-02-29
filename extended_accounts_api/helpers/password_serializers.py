from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from extended_accounts_api.models import AccountModel as Account


class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(
        self, value
    ):  ## We return the user to avoid repeating the database query in extended_accounts_api.views.ResetPassword.ResetPasswordRequestView
        try:
            account = Account.objects.get(email=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError(
                "The email provided does not match any registered on the website"
            )
        if not account.is_active:
            raise serializers.ValidationError(
                "The account associated with this e-mail isn't active"
            )
        return account


class NewPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True, validators=[validate_password])
    password_confirm = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Account
        fields = ["password", "password_confirm"]

    def update(self, instance, validated_data):
        instance.set_password(validated_data["password"])
        instance.save()
        return instance

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("The two passwords must match")
        return attrs
