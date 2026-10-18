from django.urls import path
from . import views

urlpatterns=[
    path("", views.BookingCreateView.as_view(), name="booking-create"),
    path("me/", views.MyBookingListView.as_view(), name="my-bookings"),
    path("<uuid:reference>/cancel/", views.BookingCancelView.as_view(), name="booking-cancel"),
    path("<uuid:reference>/review/", views.BookingReviewCreateView.as_view(), name="booking-review"),


]

