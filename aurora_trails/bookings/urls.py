from django.urls import path
from . import views 
urlpatterns=[
    path('',views.bookings_main_page,name='bookings_main_page')
]