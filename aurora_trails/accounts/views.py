from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from rest_framework import generics
#middleware


# Create your views here.
def accounts_main_page(request):
    return JsonResponse({"message":"Accounts main page"})


