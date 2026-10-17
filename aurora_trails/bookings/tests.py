#python manage.py test bookings -v 2

from django.test import TestCase
from datetime import timedelta
#for concurrency test 
import threading
from django.db import connection

from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import User
from tours.models import ActivityType, Location, Tour, TourSlot

from .models import Booking
from .services import create_booking

# Create your tests here.

# BOOKING CAPACITY TEST 
class BookingCapacityTests(TransactionTestCase):
    """
    Tests for booking capacity rules.

    Uses TransactionTestCase instead of TestCase so that real commits happen.
    This is required for the concurrency test, which uses separate database
    connections to verify row locking with select_for_update.
    """

    def setUp(self):
        """Create a guide, two customers and a tour slot with capacity for 2 people."""

        guide = User.objects.create_user(
            username="guide", email="guide@test.no", password="testpass123", role=User.Role.GUIDE
        )
        self.customer_a = User.objects.create_user(
            username="customer_a", email="a@test.no", password="testpass123", role=User.Role.CUSTOMER
        )
        self.customer_b = User.objects.create_user(
            username="customer_b", email="b@test.no", password="testpass123", role=User.Role.CUSTOMER
        )
        tour = Tour.objects.create(
            guide=guide,
            activity_type=ActivityType.objects.create(name="Husky Safari"),
            location=Location.objects.create(name="Alta", latitude=69.9689, longitude=23.2717),
            title="Test Tour",
            description="Test description",
            duration_minutes=120,
            price=1000,
            max_participants=2,
        )
        self.slot = TourSlot.objects.create(
            tour=tour, start_time=timezone.now() + timedelta(days=7)
        )

    def test_booking_is_rejected_when_slot_is_full(self):
        """A booking must be rejected when the slot has no available spots left."""

        create_booking(self.customer_a, self.slot.id, participants=2)

        with self.assertRaises(ValidationError):
            create_booking(self.customer_b, self.slot.id, participants=1)

        self.assertEqual(Booking.objects.count(), 1)



# CONCURRENCY TEST 
    def test_concurrent_bookings_cannot_overbook(self):
        """Two simultaneous requests for the same spots: exactly one must succeed."""
        barrier = threading.Barrier(2)
        results = []

        def attempt_booking(customer):
            try:
                barrier.wait()
                create_booking(customer, self.slot.id, participants=2)
                results.append("success")
            except ValidationError:
                results.append("rejected")
            finally:
                connection.close()

        threads = [
            threading.Thread(target=attempt_booking, args=(customer,))
            for customer in (self.customer_a, self.customer_b)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(results.count("success"), 1)
        self.assertEqual(results.count("rejected"), 1)
        self.assertEqual(Booking.objects.count(), 1)