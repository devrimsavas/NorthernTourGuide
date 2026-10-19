import django_filters
from django.utils import timezone

from .models import Tour, TourSlot


class TourFilter(django_filters.FilterSet):
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    date_from = django_filters.DateFilter(method="filter_by_dates")
    date_to = django_filters.DateFilter(method="filter_by_dates")

    class Meta:
        model = Tour
        fields = ["location", "activity_type", "difficulty"]

    def filter_by_dates(self, queryset, name, value):
        """Keep tours with at least one upcoming slot inside the requested date range."""
        date_from = self.form.cleaned_data.get("date_from")
        date_to = self.form.cleaned_data.get("date_to")

        slots = TourSlot.objects.filter(start_time__gte=timezone.now())
        if date_from:
            slots = slots.filter(start_time__date__gte=date_from)
        if date_to:
            slots = slots.filter(start_time__date__lte=date_to)

        return queryset.filter(id__in=slots.values("tour_id"))