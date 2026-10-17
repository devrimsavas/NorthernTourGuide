from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader



# Create your views here.

def main_page(request):
    return JsonResponse({"message":"Main Page of Aurora Trails App"})
