from django.urls import path

from . import views

urlpatterns = [
    path("tours/", views.GuideTourListCreateView.as_view(), name="guide-tour-list"),
    path("tours/<int:pk>/", views.GuideTourDetailView.as_view(), name="guide-tour-detail"),
    path("tours/<int:pk>/slots/", views.GuideTourSlotListCreateView.as_view(), name="guide-tour-slots"),
]