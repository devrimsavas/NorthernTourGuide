from django.urls import path

from . import views

urlpatterns = [
    path("activity-types/", views.ActivityTypeListView.as_view(), name="activity-type-list"),
    path("locations/", views.LocationListView.as_view(), name="location-list"),
]