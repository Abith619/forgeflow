import factory
from factory.django import DjangoModelFactory

from .models import Company, User


class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f"Company {n}")
    code = factory.Sequence(lambda n: f"C-{n}")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"email{n}@example.com")
    full_name = factory.Sequence(lambda n: f"User {n}")
    company = factory.SubFactory(CompanyFactory)
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        raw_password = extracted or "TestPassword123!"
        self.set_password(raw_password)

        if create:
            self.save(update_fields=["password"])
