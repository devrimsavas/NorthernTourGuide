# database lock get view response , apply work rules
from django.db import transaction
from rest_framework.exceptions import ValidationError

#models 
from tours.models import TourSlot
from .models import Booking

def create_booking(customer,slot_id,participants):
    #everything inside block a single transaction. committed after block finished 
    # in case of error , rollback 
    with transaction.atomic():
        #read slot and lock .The second request for same slot waits until first request is done
        slot=TourSlot.objects.select_for_update().get(pk=slot_id)
        if participants > slot.available_spots:
            #throw error if slot is not empty 
            raise ValidationError(
                {"participants": f"Only {slot.available_spots} spots left on this slot."}
            )
        return Booking.objects.create(
            slot=slot,
            customer=customer,
            participants=participants,
            total_price=slot.tour.price*participants,
            #not yet any payment, if there is avaliable slot reservation confirmed
            status=Booking.Status.CONFIRMED,
        )
