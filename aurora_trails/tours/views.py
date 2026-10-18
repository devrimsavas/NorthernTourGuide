from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader 
from django.db.models import Prefetch
from django.utils import timezone
import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .weather import forecast_at, get_forecast
from .aurora import aurora_chance,get_kp_forecast,kp_at


#list api view imports
from rest_framework import generics
from .models import Tour,TourSlot
from .serializers import TourSerializer,TourDetailSerializer,GuideTourSerializer,GuideTourSlotSerializer
from accounts.permissions import IsGuide
from bookings.models import Review
from bookings.serializers import ReviewSerializer

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


class TourForecastView(APIView):
    def get(self, request, pk):
        tour = get_object_or_404(Tour.objects.select_related("location"), pk=pk, is_active=True)
        upcoming_slots = tour.slots.filter(start_time__gte=timezone.now())

        try:
            weather_data = get_forecast(tour.location.latitude, tour.location.longitude)
        except requests.RequestException:
            return Response(
                {"detail": "Weather forecast is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            kp_data = get_kp_forecast()
        except requests.RequestException:
            kp_data = None

        return Response(
            {
                "location": tour.location.name,
                "sources": [
                    "Weather: MET Norway (api.met.no), CC BY 4.0",
                    "Kp index: NOAA Space Weather Prediction Center",
                ],
                "slots": [self._slot_forecast(slot, weather_data, kp_data) for slot in upcoming_slots],
            }
        )

    def _slot_forecast(self, slot, weather_data, kp_data):
        weather = forecast_at(weather_data, slot.start_time)
        kp = kp_at(kp_data, slot.start_time) if kp_data else None
        cloud = weather["cloud_area_fraction"] if weather else None

        return {
            "slot_id": slot.id,
            "start_time": timezone.localtime(slot.start_time),
            "forecast": weather,
            "aurora": {"kp": kp, "chance": aurora_chance(kp, cloud)} if kp is not None else None,
        }


class TourReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(booking__slot__tour_id=self.kwargs["pk"]).select_related(
            "booking__customer"
        )