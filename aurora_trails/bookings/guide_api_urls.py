from django.urls import path

from . import views

urlpatterns = [
    path("bookings/", views.GuideBookingListView.as_view(), name="guide-booking-list"),
]