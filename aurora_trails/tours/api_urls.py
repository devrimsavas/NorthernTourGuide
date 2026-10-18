#tour Apis 
from django.urls import path 
from . import views
urlpatterns=[
    path("",views.TourListView.as_view(),name="tour-list"),
    path("<int:pk>/",views.TourDetailView.as_view(),name="tour-detail"),
    path("<int:pk>/forecast/", views.TourForecastView.as_view(), name="tour-forecast"),
    path("<int:pk>/reviews/", views.TourReviewListView.as_view(), name="tour-reviews"),
]