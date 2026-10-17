from django.utils import timezone
from rest_framework import serializers
#models 
from .models import Booking

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

    