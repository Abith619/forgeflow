from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Company, User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(required=True)
    company_name = serializers.CharField(required=True)
    company_code = serializers.CharField(required=True)

    def validate_company_code(self, value):
        company_code = value.strip().upper()
        if Company.objects.filter(code=company_code).exists():
            raise serializers.ValidationError("Company with this code already exists")
        return company_code

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("User with this email already exists")
        return email

    def validate(self, attrs):
        user = User(
            email=attrs['email'],
            full_name=attrs['full_name'],
        )
        try:
            validate_password(attrs['password'], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"password": exc.messages}
            )
        return attrs

    def create(self, validated_data):
        company_name = validated_data.pop("company_name")
        company_code = validated_data.pop("company_code")

        with transaction.atomic():
            company = Company.objects.create(
                name=company_name,
                code=company_code,
            )

            user = User.objects.create_user(
                company=company,
                **validated_data,
            )

        return user

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "code"]

class MeSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'company']

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)