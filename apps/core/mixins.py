

class CompanyScopedQuerysetMixin:
    company_field = "company"

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = getattr(self.request.user, "company_id", None)
        if not company_id:
            return qs.none()
        return qs.filter(**{self.company_field: company_id})
