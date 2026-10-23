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
            if slot.available_spots == 0:
                message = "This slot is sold out."
            elif slot.available_spots == 1:
                message = "Only 1 spot left on this slot."
            else:
                message = f"Only {slot.available_spots} spots left on this slot."
            raise ValidationError({"participants": message})
        return Booking.objects.create(
            slot=slot,
            customer=customer,
            participants=participants,
            total_price=slot.tour.price*participants,
            #not yet any payment, if there is avaliable slot reservation confirmed
            status=Booking.Status.CONFIRMED,
        )

def tour_has_ended(booking):
    tour_end = booking.slot.start_time + timedelta(minutes=booking.slot.tour.duration_minutes)
    return tour_end <= timezone.now()


def has_review(booking):
    return hasattr(booking, "review")


def cancel_error(booking):
    """Return why the booking cannot be cancelled, or None if it can."""
    if booking.status == Booking.Status.CANCELLED:
        return "This booking is already cancelled."
    if booking.slot.start_time <= timezone.now():
        return "Bookings cannot be cancelled after the tour has started."
    return None


def review_error(booking):
    """Return why the booking cannot be reviewed, or None if it can."""
    if booking.status != Booking.Status.CONFIRMED:
        return "Only confirmed bookings can be reviewed."
    if not tour_has_ended(booking):
        return "You can review a tour only after it has ended."
    if has_review(booking):
        return "This booking has already been reviewed."
    return None


def cancel_booking(booking):
    error = cancel_error(booking)
    if error:
        raise ValidationError({"status": error})

    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status"])
    return booking


def create_review(booking, rating, comment=""):
    error = review_error(booking)
    if error:
        raise ValidationError({"booking": error})

    return Review.objects.create(booking=booking, rating=rating, comment=comment)