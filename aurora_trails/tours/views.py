from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader 
from django.db.models import Prefetch
from django.utils import timezone

#list api view imports
from rest_framework import generics
from .models import Tour,TourSlot
from .serializers import TourSerializer,TourDetailSerializer,GuideTourSerializer,GuideTourSlotSerializer
from accounts.permissions import IsGuide

# Create your views here.
def tours_main_page(request):
    return JsonResponse({"message":"Tours main page"})


class TourListView(generics.ListAPIView):
    serializer_class=TourSerializer
    queryset=Tour.objects.filter(is_active=True).select_related(
        "guide","activity_type","location"
    )

# tour detail
class TourDetailView(generics.RetrieveAPIView):
    serializer_class=TourDetailSerializer
    def get_queryset(self):
        upcoming_slots=TourSlot.objects.filter(start_time__gte=timezone.now())
        return (
            Tour.objects.filter(is_active=True)
            .select_related("guide", "activity_type", "location")
            .prefetch_related(Prefetch("slots", queryset=upcoming_slots))

        )

class GuideTourListCreateView(generics.ListCreateAPIView):
    serializer_class = GuideTourSerializer
    permission_classes = [IsGuide]

    def get_queryset(self):
        return Tour.objects.filter(guide=self.request.user)

    def perform_create(self, serializer):
        serializer.save(guide=self.request.user)


class GuideTourDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = GuideTourSerializer
    permission_classes = [IsGuide]

    def get_queryset(self):
        return Tour.objects.filter(guide=self.request.user)


class GuideTourSlotListCreateView(generics.ListCreateAPIView):
    serializer_class = GuideTourSlotSerializer
    permission_classes = [IsGuide]

    def get_tour(self):
        return get_object_or_404(Tour, pk=self.kwargs["pk"], guide=self.request.user)

    def get_queryset(self):
        return self.get_tour().slots.all()

    def perform_create(self, serializer):
        tour = self.get_tour()
        start_time = serializer.validated_data["start_time"]
        if tour.slots.filter(start_time=start_time).exists():
            raise ValidationError({"start_time": "This tour already has a slot at this time."})
        serializer.save(tour=tour)