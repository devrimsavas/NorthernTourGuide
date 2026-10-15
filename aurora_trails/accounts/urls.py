from django.urls import path
from . import views 
urlpatterns=[
    path('',views.accounts_main_page,name='accounts_main_page')
]
