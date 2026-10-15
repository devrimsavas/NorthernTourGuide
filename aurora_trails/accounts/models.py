from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    class Role(models.TextChoices):
        GUIDE="guide","Guide"
        CUSTOMER="customer","Customer"
        ADMIN="admin","Admin"
    email=models.EmailField(unique=True)
    role=models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    USERNAME_FIELD="email"
    REQUIRED_FIELDS=["username"]


class GuideProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="guide_profile",
    )
    bio = models.TextField(blank=True)
    languages = models.CharField(max_length=200, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    #add relations 
    base_location=models.ForeignKey(
        "tours.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guides"
    )

    def __str__(self):
        return self.user.email

