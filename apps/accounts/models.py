from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Company(TimeStampedModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Companies"
        constraints = [
            models.CheckConstraint(condition=~Q(code=""), name="company_code_not_empty"),
        ]

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        company = extra_fields.pop("company", None)
        if company is None:
            raise ValueError("Company is required")
        if isinstance(company, Company):
            pass
        else:
            company = Company.objects.get(pk=company)
        extra_fields["company"] = company
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def unlink_user(self, user):
        if user:
            return "You cannot delete any user"

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_active") is not True:
            raise ValueError("Superuser must have is_active=True.")
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="users", null=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['company']
    objects = UserManager()

    def __str__(self):
        return self.email