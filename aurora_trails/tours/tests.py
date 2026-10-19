from datetime import timedelta
from unittest.mock import patch 
import requests

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from bookings.models import Booking

from .models import ActivityType, Location, Tour, TourSlot,TourImage
import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from datetime import UTC

from django.test import SimpleTestCase

from .aurora import aurora_chance


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

def make_kp_response(moment, kp):
    """Build a fake NOAA Kp forecast with a single 3-hour window containing the given moment."""
    utc = moment.astimezone(UTC)
    window_start = utc.replace(hour=utc.hour - utc.hour % 3, minute=0, second=0, microsecond=0)
    return [
        {
            "time_tag": window_start.strftime("%Y-%m-%dT%H:%M:%S"),
            "kp": kp,
            "observed": "predicted",
            "noaa_scale": None,
        }
    ]


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

        kp_patcher = patch("tours.views.get_kp_forecast", return_value=[])
        self.mock_get_kp_forecast = kp_patcher.start()
        self.addCleanup(kp_patcher.stop)


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


    @patch("tours.views.get_forecast")
    def test_aurora_chance_is_returned_for_upcoming_slot(self, mock_get_forecast):
        """High Kp with a clear sky gives a high aurora chance."""
        mock_get_forecast.return_value = make_met_response(self.soon_slot.start_time)
        self.mock_get_kp_forecast.return_value = make_kp_response(self.soon_slot.start_time, kp=4.67)

        response = self.client.get(self.url)

        soon = next(s for s in response.data["slots"] if s["slot_id"] == self.soon_slot.id)
        self.assertEqual(soon["aurora"]["kp"], 4.67)
        self.assertEqual(soon["aurora"]["chance"], "high")

    @patch("tours.views.get_forecast")
    def test_weather_is_still_returned_when_noaa_is_unavailable(self, mock_get_forecast):
        """If NOAA fails, the weather forecast is still returned and aurora is null."""
        mock_get_forecast.return_value = make_met_response(self.soon_slot.start_time)
        self.mock_get_kp_forecast.side_effect = requests.RequestException

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        soon = next(s for s in response.data["slots"] if s["slot_id"] == self.soon_slot.id)
        self.assertIsNotNone(soon["forecast"])
        self.assertIsNone(soon["aurora"])


class AuroraChanceTests(SimpleTestCase):
    """Unit tests for the aurora chance rule. No database or HTTP needed."""

    def test_cloudy_sky_gives_low_chance_even_with_high_kp(self):
        self.assertEqual(aurora_chance(kp=6, cloud_area_fraction=90), "low")

    def test_strong_kp_and_clear_sky_gives_high_chance(self):
        self.assertEqual(aurora_chance(kp=4.33, cloud_area_fraction=20), "high")

    def test_moderate_kp_gives_medium_chance(self):
        self.assertEqual(aurora_chance(kp=2.5, cloud_area_fraction=50), "medium")

    def test_missing_data_gives_no_chance(self):
        self.assertIsNone(aurora_chance(kp=None, cloud_area_fraction=20))   



TINY_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00"
    b",\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def make_image(name):
    return SimpleUploadedFile(name, TINY_GIF, content_type="image/gif")


class TourImageApiTests(APITestCase):
    """Tests for tour images: cover image in the list, all images in the detail."""

    def setUp(self):
        """Use a temporary media folder and create a tour with two images."""
        media_dir = tempfile.mkdtemp()
        media_override = override_settings(MEDIA_ROOT=media_dir)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.addCleanup(shutil.rmtree, media_dir, ignore_errors=True)

        guide = User.objects.create_user(
            username="guide", email="guide@test.no", password="testpass123", role=User.Role.GUIDE
        )
        activity = ActivityType.objects.create(name="Husky Safari")
        location = Location.objects.create(name="Alta", latitude=69.9689, longitude=23.2717)
        tour_data = {
            "guide": guide,
            "activity_type": activity,
            "location": location,
            "description": "Test description",
            "duration_minutes": 120,
            "price": 1000,
            "max_participants": 8,
        }
        self.tour = Tour.objects.create(title="Tour With Images", **tour_data)
        self.tour_without_images = Tour.objects.create(title="Tour Without Images", **tour_data)

        TourImage.objects.create(tour=self.tour, image=make_image("second.gif"), order=1)
        TourImage.objects.create(tour=self.tour, image=make_image("cover.gif"), order=0)

    def find_tour(self, response, tour):
        return next(t for t in response.data["results"] if t["id"] == tour.id)

    def test_cover_image_is_the_first_image_by_order(self):
        """The cover is the image with the lowest order, returned as a full URL."""
        response = self.client.get(reverse("tour-list"))

        cover = self.find_tour(response, self.tour)["cover_image"]
        self.assertTrue(cover.startswith("http://testserver/media/tours/"))
        self.assertIn("cover", cover)

    def test_cover_image_is_null_without_images(self):
        """A tour without images has no cover image."""
        response = self.client.get(reverse("tour-list"))

        self.assertIsNone(self.find_tour(response, self.tour_without_images)["cover_image"])

    def test_detail_lists_all_images_in_order(self):
        """The tour detail returns every image, sorted by order."""
        response = self.client.get(reverse("tour-detail", args=[self.tour.id]))

        images = response.data["images"]
        self.assertEqual(len(images), 2)
        self.assertIn("cover", images[0]["image"])
        self.assertIn("second", images[1]["image"])


class TourFilterApiTests(APITestCase):
    """Tests for tour list filters and the lookup lists used by the frontend dropdowns."""

    def setUp(self):
        """Create two tours in different locations, with slots placed relative to today."""
        guide = User.objects.create_user(
            username="guide", email="guide@test.no", password="testpass123", role=User.Role.GUIDE
        )
        self.alta = Location.objects.create(name="Alta", latitude=69.9689, longitude=23.2717)
        tromso = Location.objects.create(name="Tromsø", latitude=69.6492, longitude=18.9553)
        husky = ActivityType.objects.create(name="Husky Safari")
        aurora = ActivityType.objects.create(name="Northern Lights Tour")

        self.husky_tour = Tour.objects.create(
            guide=guide, activity_type=husky, location=self.alta, title="Husky Tour",
            description="Test", duration_minutes=180, price=2490, max_participants=8,
        )
        self.aurora_tour = Tour.objects.create(
            guide=guide, activity_type=aurora, location=tromso, title="Aurora Tour",
            description="Test", duration_minutes=240, price=1890, max_participants=12,
        )

        now = timezone.now()
        TourSlot.objects.create(tour=self.husky_tour, start_time=now + timedelta(days=30))
        TourSlot.objects.create(tour=self.aurora_tour, start_time=now + timedelta(days=10))
        TourSlot.objects.create(tour=self.aurora_tour, start_time=now + timedelta(days=60))

        self.url = reverse("tour-list")

    def titles(self, response):
        return {tour["title"] for tour in response.data["results"]}

    def day(self, days_from_today):
        return (timezone.localdate() + timedelta(days=days_from_today)).isoformat()

    def test_filter_by_location(self):
        """Only tours in the requested location are returned."""
        response = self.client.get(self.url, {"location": self.alta.id})

        self.assertEqual(self.titles(response), {"Husky Tour"})

    def test_filter_by_max_price(self):
        """Tours more expensive than max_price are excluded."""
        response = self.client.get(self.url, {"max_price": 2000})

        self.assertEqual(self.titles(response), {"Aurora Tour"})

    def test_date_range_must_match_a_single_slot(self):
        """A tour with slots only before and after the range is not returned."""
        response = self.client.get(self.url, {"date_from": self.day(25), "date_to": self.day(35)})

        self.assertEqual(self.titles(response), {"Husky Tour"})

    def test_invalid_date_returns_400(self):
        """A malformed date is rejected with a clear error."""
        response = self.client.get(self.url, {"date_from": "tomorrow"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lookup_lists_are_sorted_by_name(self):
        """Locations and activity types come back in alphabetical order."""
        locations = self.client.get(reverse("location-list")).data
        activities = self.client.get(reverse("activity-type-list")).data

        self.assertEqual([l["name"] for l in locations], ["Alta", "Tromsø"])
        self.assertEqual([a["name"] for a in activities], ["Husky Safari", "Northern Lights Tour"])

    def test_tour_list_is_paginated(self):
        """The tour list returns pages with a total count and a link to the next page."""
        response = self.client.get(self.url, {"page_size": 1})

        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])