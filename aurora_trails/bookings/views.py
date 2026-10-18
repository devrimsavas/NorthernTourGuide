from django.shortcuts import render
from django.http import HttpRequest ,JsonResponse
from django.template import loader 
from rest_framework import generics

from accounts.permissions import IsCustomer
from .models import Booking
from .serializers import BookingCreateSerializer,BookingListSerializer

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import cancel_booking, create_booking


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

#only logged customers' reservations 

class MyBookingListView(generics.ListAPIView):
    serializer_class = BookingListSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return Booking.objects.filter(customer=self.request.user).select_related("slot__tour")


class BookingCancelView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request, reference):
        booking = get_object_or_404(
            Booking.objects.select_related("slot__tour"),
            reference=reference,
            customer=request.user,
        )
        cancel_booking(booking)
        return Response(BookingListSerializer(booking).data)