# database lock get view response , apply work rules
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from datetime import timedelta
from .models import Booking,Review

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

# cancel reservation soft delete 
def cancel_booking(booking):
    if booking.status == Booking.Status.CANCELLED:
        raise ValidationError({"status": "This booking is already cancelled."})

    if booking.slot.start_time <= timezone.now():
        raise ValidationError({"status": "Bookings cannot be cancelled after the tour has started."})

    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status"])
    return booking

#create review 
def create_review(booking, rating, comment=""):
    if booking.status != Booking.Status.CONFIRMED:
        raise ValidationError({"booking": "Only confirmed bookings can be reviewed."})

    tour_end = booking.slot.start_time + timedelta(minutes=booking.slot.tour.duration_minutes)
    if tour_end > timezone.now():
        raise ValidationError({"booking": "You can review a tour only after it has ended."})

    if Review.objects.filter(booking=booking).exists():
        raise ValidationError({"booking": "This booking has already been reviewed."})

    return Review.objects.create(booking=booking, rating=rating, comment=comment)