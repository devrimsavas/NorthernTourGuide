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
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Booking,Review
from .services import create_booking,cancel_booking

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

# CANCEL RESERVATION
    def test_cancelling_a_booking_frees_up_spots(self):
        """Cancelling a booking must make its spots available again."""
        booking = create_booking(self.customer_a, self.slot.id, participants=2)
        self.assertEqual(self.slot.available_spots, 0)

        cancel_booking(booking)

        self.assertEqual(self.slot.available_spots, 2)

    def test_booking_cannot_be_cancelled_twice(self):
        """An already cancelled booking must not be cancelled again."""
        booking = create_booking(self.customer_a, self.slot.id, participants=2)
        cancel_booking(booking)

        with self.assertRaises(ValidationError):
            cancel_booking(booking)

#review test (mock)
class ReviewApiTests(APITestCase):
    """Tests for review rules: only customers with a confirmed, finished booking can review."""

    def setUp(self):
        """Create a finished slot, an upcoming slot and bookings for two customers."""
        guide = User.objects.create_user(
            username="guide", email="guide@test.no", password="testpass123", role=User.Role.GUIDE
        )
        self.customer = User.objects.create_user(
            username="lukas",
            email="lukas@test.no",
            password="testpass123",
            role=User.Role.CUSTOMER,
            first_name="Lukas",
            last_name="Weber",
        )
        self.other_customer = User.objects.create_user(
            username="emma", email="emma@test.no", password="testpass123", role=User.Role.CUSTOMER
        )
        self.tour = Tour.objects.create(
            guide=guide,
            activity_type=ActivityType.objects.create(name="Husky Safari"),
            location=Location.objects.create(name="Alta", latitude=69.9689, longitude=23.2717),
            title="Test Tour",
            description="Test description",
            duration_minutes=120,
            price=1000,
            max_participants=8,
        )
        finished_slot = TourSlot.objects.create(
            tour=self.tour, start_time=timezone.now() - timedelta(days=1)
        )
        upcoming_slot = TourSlot.objects.create(
            tour=self.tour, start_time=timezone.now() + timedelta(days=7)
        )
        self.finished_booking = Booking.objects.create(
            slot=finished_slot,
            customer=self.customer,
            participants=2,
            total_price=2000,
            status=Booking.Status.CONFIRMED,
        )
        self.upcoming_booking = Booking.objects.create(
            slot=upcoming_slot,
            customer=self.customer,
            participants=2,
            total_price=2000,
            status=Booking.Status.CONFIRMED,
        )
        self.client.force_authenticate(user=self.customer)

    def review_url(self, booking):
        return reverse("booking-review", args=[booking.reference])

    def test_customer_can_review_a_finished_tour(self):
        """A review on a finished tour is saved and shown publicly with the first name only."""
        response = self.client.post(
            self.review_url(self.finished_booking), {"rating": 5, "comment": "Amazing dogs!"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        public = self.client.get(reverse("tour-reviews", args=[self.tour.id]))
        self.assertEqual(len(public.data), 1)
        self.assertEqual(public.data[0]["reviewer"], "Lukas")
        self.assertEqual(public.data[0]["rating"], 5)

    def test_cannot_review_before_tour_ends(self):
        """A tour that has not ended yet cannot be reviewed."""
        response = self.client.post(self.review_url(self.upcoming_booking), {"rating": 4})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 0)

    def test_cannot_review_the_same_booking_twice(self):
        """Only one review is allowed per booking."""
        self.client.post(self.review_url(self.finished_booking), {"rating": 5})

        response = self.client.post(self.review_url(self.finished_booking), {"rating": 1})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)

    def test_cannot_review_a_cancelled_booking(self):
        """Cancelled bookings cannot be reviewed."""
        self.finished_booking.status = Booking.Status.CANCELLED
        self.finished_booking.save()

        response = self.client.post(self.review_url(self.finished_booking), {"rating": 5})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_review_another_customers_booking(self):
        """A customer gets 404 when trying to review someone else's booking."""
        self.client.force_authenticate(user=self.other_customer)

        response = self.client.post(self.review_url(self.finished_booking), {"rating": 1})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rating_must_be_between_1_and_5(self):
        """Ratings outside the 1-5 range are rejected."""
        response = self.client.post(self.review_url(self.finished_booking), {"rating": 6})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tour_list_shows_average_rating_and_review_count(self):
        """The tour list includes the average rating and the number of reviews."""
        second_booking = Booking.objects.create(
            slot=self.finished_booking.slot,
            customer=self.other_customer,
            participants=1,
            total_price=1000,
            status=Booking.Status.CONFIRMED,
        )
        Review.objects.create(booking=self.finished_booking, rating=5)
        Review.objects.create(booking=second_booking, rating=4)

        response = self.client.get(reverse("tour-list"))

        tour = next(t for t in response.data if t["id"] == self.tour.id)
        self.assertEqual(tour["average_rating"], 4.5)
        self.assertEqual(tour["review_count"], 2)