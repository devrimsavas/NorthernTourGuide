from django.urls import path
from . import views
urlpatterns=[
    path('',views.tours_main_page,name='tours_main_page')
]