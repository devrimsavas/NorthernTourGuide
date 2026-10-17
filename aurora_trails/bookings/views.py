from django.shortcuts import render
from django.http import HttpRequest ,JsonResponse
from django.template import loader 
from rest_framework import generics

from accounts.permissions import IsCustomer

from .serializers import BookingCreateSerializer
from .services import create_booking


# Create your views here.
def bookings_main_page(request):
    return JsonResponse({"message":"Bookings main page"})


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [IsCustomer]

    def perform_create(self, serializer):
        booking = create_booking(
            customer=self.request.user,
            slot_id=serializer.validated_data["slot"].id,
            participants=serializer.validated_data["participants"],
        )
        serializer.instance = booking