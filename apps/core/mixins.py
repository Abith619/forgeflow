class CompanyScopedQuerysetMixin:

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = getattr(self.request.user, "company_id", None)
        return qs.for_company(company_id)
