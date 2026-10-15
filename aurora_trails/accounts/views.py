from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader

# Create your views here.
def accounts_main_page(request):
    return JsonResponse({"message":"Accounts main page"})