from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from rest_framework import generics,status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from rest_framework import response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import MeSerializer, RegisterSerializer,GuideSerializer
from rest_framework.response import Response
from .models import User

#middleware


# Create your views here.
def accounts_main_page(request):
    return JsonResponse({"message":"Accounts main page"})


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": serializer.data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )

class MeView(generics.RetrieveAPIView):
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


def public_guides():
    return (
        User.objects.filter(role=User.Role.GUIDE, is_active=True, guide_profile__isnull=False)
        .select_related("guide_profile__base_location")
        .order_by("first_name")
    )


class GuideListView(generics.ListAPIView):
    serializer_class = GuideSerializer
    permission_classes = [AllowAny]
    queryset = public_guides()


class GuideDetailView(generics.RetrieveAPIView):
    serializer_class = GuideSerializer
    permission_classes = [AllowAny]
    queryset = public_guides()