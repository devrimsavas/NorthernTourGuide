from datetime import timedelta
from unittest.mock import patch 
import requests

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from bookings.models import Booking

from .models import ActivityType, Location, Tour, TourSlot


class GuideTourApiTests(APITestCase):
    """Tests for the guide endpoints: ownership, role checks and capacity rules."""

    def setUp(self):
        """Create two guides, a customer and a tour owned by the first guide."""
        self.kari = User.objects.create_user(
            username="kari", email="kari@test.no", password="testpass123", role=User.Role.GUIDE
        )
        self.ola = User.objects.create_user(
            username="ola", email="ola@test.no", password="testpass123", role=User.Role.GUIDE
        )
        self.customer = User.objects.create_user(
            username="customer", email="customer@test.no", password="testpass123", role=User.Role.CUSTOMER
        )
        self.activity = ActivityType.objects.create(name="Husky Safari")
        self.location = Location.objects.create(name="Alta", latitude=69.9689, longitude=23.2717)
        self.tour = Tour.objects.create(
            guide=self.kari,
            activity_type=self.activity,
            location=self.location,
            title="Kari's Tour",
            description="Test description",
            duration_minutes=120,
            price=1000,
            max_participants=8,
        )

    def test_guide_can_create_tour(self):
        """A guide creates a tour and automatically becomes its owner."""
        self.client.force_authenticate(user=self.ola)

        response = self.client.post(
            reverse("guide-tour-list"),
            {
                "title": "Ola's Tour",
                "description": "Test description",
                "activity_type": self.activity.id,
                "location": self.location.id,
                "duration_minutes": 90,
                "price": "800.00",
                "max_participants": 6,
                "is_active": True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tour.objects.get(pk=response.data["id"]).guide, self.ola)

    def test_guide_cannot_edit_another_guides_tour(self):
        """A guide gets 404 when trying to update a tour owned by another guide."""
        self.client.force_authenticate(user=self.ola)

        response = self.client.patch(
            reverse("guide-tour-detail", args=[self.tour.id]), {"price": "1.00"}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.price, 1000)

    def test_customer_cannot_access_guide_endpoints(self):
        """Customers must be rejected by the guide endpoints."""
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(reverse("guide-tour-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_capacity_cannot_be_reduced_below_booked_spots(self):
        """A guide cannot lower max participants below the spots already booked."""
        slot = TourSlot.objects.create(tour=self.tour, start_time=timezone.now() + timedelta(days=7))
        Booking.objects.create(
            slot=slot,
            customer=self.customer,
            participants=5,
            total_price=5000,
            status=Booking.Status.CONFIRMED,
        )
        self.client.force_authenticate(user=self.kari)

        response = self.client.patch(
            reverse("guide-tour-detail", args=[self.tour.id]), {"max_participants": 4}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


#dummy request for met

def make_met_response(moment):
    """Build a minimal fake MET Norway response with a single forecast at the given moment."""
    return {
        "properties": {
            "timeseries": [
                {
                    "time": moment.isoformat(),
                    "data": {
                        "instant": {
                            "details": {
                                "air_temperature": -12.5,
                                "cloud_area_fraction": 5.0,
                                "wind_speed": 2.1,
                            }
                        },
                        "next_1_hours": {"summary": {"symbol_code": "clearsky_night"}},
                    },
                }
            ]
        }
    }


class TourForecastApiTests(APITestCase):
    """Tests for the forecast endpoint. MET Norway is mocked, no real requests are made."""

    def setUp(self):
        """Create a tour with one slot tomorrow and one slot far beyond the forecast range."""
        guide = User.objects.create_user(
            username="guide", email="guide@test.no", password="testpass123", role=User.Role.GUIDE
        )
        self.tour = Tour.objects.create(
            guide=guide,
            activity_type=ActivityType.objects.create(name="Northern Lights Tour"),
            location=Location.objects.create(name="Tromsø", latitude=69.6492, longitude=18.9553),
            title="Aurora Test Tour",
            description="Test description",
            duration_minutes=240,
            price=1500,
            max_participants=10,
        )
        self.soon_slot = TourSlot.objects.create(
            tour=self.tour, start_time=timezone.now() + timedelta(days=1)
        )
        self.far_slot = TourSlot.objects.create(
            tour=self.tour, start_time=timezone.now() + timedelta(days=30)
        )
        self.url = reverse("tour-forecast", args=[self.tour.id])

    @patch("tours.views.get_forecast")
    def test_forecast_is_returned_for_upcoming_slot(self, mock_get_forecast):
        """A slot within the forecast range gets its weather data."""
        mock_get_forecast.return_value = make_met_response(self.soon_slot.start_time)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        soon = next(s for s in response.data["slots"] if s["slot_id"] == self.soon_slot.id)
        self.assertEqual(soon["forecast"]["symbol_code"], "clearsky_night")
        self.assertEqual(soon["forecast"]["cloud_area_fraction"], 5.0)

    @patch("tours.views.get_forecast")
    def test_forecast_is_null_beyond_forecast_range(self, mock_get_forecast):
        """A slot too far in the future gets no forecast instead of a wrong one."""
        mock_get_forecast.return_value = make_met_response(self.soon_slot.start_time)

        response = self.client.get(self.url)

        far = next(s for s in response.data["slots"] if s["slot_id"] == self.far_slot.id)
        self.assertIsNone(far["forecast"])

    @patch("tours.views.get_forecast")
    def test_returns_503_when_met_norway_is_unavailable(self, mock_get_forecast):
        """If MET Norway cannot be reached, the API answers 503 instead of crashing."""
        mock_get_forecast.side_effect = requests.RequestException

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)