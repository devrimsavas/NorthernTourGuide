from django.shortcuts import render
from django.http import HttpRequest ,JsonResponse
from django.template import loader 

# Create your views here.
def bookings_main_page(request):
    return JsonResponse({"message":"Bookings main page"})