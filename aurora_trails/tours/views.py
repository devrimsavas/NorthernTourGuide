from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader 
from django.db.models import Prefetch
from django.utils import timezone

#list api view imports
from rest_framework import generics
from .models import Tour,TourSlot
from .serializers import TourSerializer,TourDetailSerializer

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