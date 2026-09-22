from factory.django import DjangoModelFactory
from apps.accounts.models import Company, User
import factory

class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f"Company {n}")
    code = factory.Sequence(lambda n: f"C-{n}")

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"email{n}@example.com")
    full_name = factory.Sequence(lambda n: f"User {n}")
    company = factory.SubFactory(CompanyFactory)
    is_active = True
    is_staff = False
    is_superuser = False