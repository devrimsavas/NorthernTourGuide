from django.utils import timezone
from rest_framework import serializers
#models 
from .models import Booking,Review

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model=Booking
        fields=["reference", "slot", "participants", "total_price", "status", "created_at"]
        #visible fields 
        read_only_fields = ["reference", "total_price", "status", "created_at"]
        #minimum 1 person 
        extra_kwargs = {"participants": {"min_value": 1}}
    #validation 
    def validate_slot(self, slot):
        if slot.start_time <= timezone.now():
            raise serializers.ValidationError("This tour slot has already started.")
        if not slot.tour.is_active:
            raise serializers.ValidationError("This tour is not available.")
        return slot

#customer can see his own tours and date
class BookingListSerializer(serializers.ModelSerializer):
    tour=serializers.CharField(source="slot.tour.title",read_only=True)
    start_time=serializers.DateTimeField(source="slot.start_time", read_only=True)
    class Meta:
        model=Booking
        fields=["reference", "tour", "start_time", "participants", "total_price", "status", "created_at"]


#customers' review it will show only customer's name and country (i mean tourist, visitor )
class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["rating", "comment", "created_at"]
        read_only_fields = ["created_at"]
        extra_kwargs = {"rating": {"min_value": 1, "max_value": 5}}


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.CharField(source="booking.customer.first_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "reviewer", "rating", "comment", "created_at"]

class GuideBookingSerializer(serializers.ModelSerializer):
    tour = serializers.CharField(source="slot.tour.title", read_only=True)
    start_time = serializers.DateTimeField(source="slot.start_time", read_only=True)
    customer_name = serializers.CharField(source="customer.get_full_name", read_only=True)
    customer_email = serializers.EmailField(source="customer.email", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "reference",
            "tour",
            "slot",
            "start_time",
            "customer_name",
            "customer_email",
            "participants",
            "status",
            "created_at",
        ]