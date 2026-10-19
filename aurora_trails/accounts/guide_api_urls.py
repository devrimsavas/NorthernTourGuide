from django.urls import path

from . import views

urlpatterns = [
    path("", views.GuideListView.as_view(), name="guide-list"),
    path("<int:pk>/", views.GuideDetailView.as_view(), name="guide-detail"),
]