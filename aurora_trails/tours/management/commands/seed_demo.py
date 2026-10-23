from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import GuideProfile, User
from tours.models import ActivityType, Location

DEMO_PASSWORD = "AuroraDemo2026"

LOCATIONS = [
    ("Tromsø", 69.6492, 18.9553),
    ("Alta", 69.9689, 23.2717),
    ("Lofoten", 68.2342, 14.5687),
    ("Karasjok", 69.4719, 25.5112),
]

ACTIVITIES = {
    "Husky Safari": (
        "Glide through snowy Arctic landscapes on a sled pulled by a team of energetic huskies. "
        "An unforgettable way to experience the silence and beauty of the northern wilderness."
    ),
    "Northern Lights Tour": (
        "Head away from the city lights in search of the aurora borealis dancing across the polar "
        "night sky. Experienced guides take you to the best viewing spots based on weather and aurora forecasts."
    ),
    "Snowshoe Hiking": (
        "Explore quiet forests and open snowfields on snowshoes, no prior experience needed. "
        "A peaceful, easy-paced way to discover the Arctic winter up close."
    ),
    "Sami Culture Experience": (
        "Meet Sami hosts in a traditional lavvu tent and learn about the reindeer herding life that has "
        "shaped the Arctic for centuries. Feed the reindeer, listen to stories and joik by the fire, "
        "and taste traditional Sami food."
    ),
}

GUIDES = [
    {
        "email": "ola.nordmann@auroratrails.test",
        "first_name": "Ola",
        "last_name": "Nordmann",
        "base_location": "Alta",
        "languages": "English, Norwegian",
        "years_of_experience": 5,
        "bio": (
            "Hi, I'm Ola! I grew up in Alta and have spent the last five years guiding visitors through "
            "the Arctic wilderness I call home. My goal is simple: to share the magic of Finnmark and make "
            "sure you go home with stories you'll never forget."
        ),
    },
    {
        "email": "kari.nordmann@auroratrails.test",
        "first_name": "Kari",
        "last_name": "Nordmann",
        "base_location": "Tromsø",
        "languages": "English, Norwegian, German",
        "years_of_experience": 8,
        "bio": (
            "Hei! I'm Kari, a Tromsø local who traded an office job for snowshoes eight years ago. I love "
            "showing guests the quiet side of the Arctic: frozen fjords, snowy forests and, if we're lucky, "
            "the aurora lighting up the sky."
        ),
    },
]

CUSTOMERS = [
    {"email": "lukas.weber@example.test", "first_name": "Lukas", "last_name": "Weber"},
    {"email": "emma.johansson@example.test", "first_name": "Emma", "last_name": "Johansson"},
    {"email": "alex.smith@example.test", "first_name": "Alex", "last_name": "Smith"},
]


class Command(BaseCommand):
    help = "Create demo data: locations, activities, guides, customers, tours, slots, bookings and reviews."

    @transaction.atomic
    def handle(self, *args, **options):
        self.verbosity = options["verbosity"]
        self.stdout.write("Seeding demo data...")

        self.locations = self.seed_locations()
        self.activities = self.seed_activities()
        self.guides = self.seed_guides()
        self.customers = self.seed_customers()

        self.stdout.write(self.style.SUCCESS("Done."))

    # Helpers

    def log(self, message):
        if self.verbosity >= 2:
            self.stdout.write(f"  {message}")

    def summary(self, label, count):
        self.stdout.write(f"{label}: {count}")

    def get_or_create_user(self, email, first_name, last_name, role):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": email, "first_name": first_name, "last_name": last_name, "role": role},
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        self.log(f"{'Created' if created else 'Found'} {role} {email}")
        return user

    # Sections

    def seed_locations(self):
        locations = {}
        for name, latitude, longitude in LOCATIONS:
            location, created = Location.objects.update_or_create(
                name=name, defaults={"latitude": latitude, "longitude": longitude}
            )
            locations[name] = location
            self.log(f"{'Created' if created else 'Updated'} location {name}")
        self.summary("Locations", len(locations))
        return locations

    def seed_activities(self):
        activities = {}
        for name, description in ACTIVITIES.items():
            activity, created = ActivityType.objects.update_or_create(
                name=name, defaults={"description": description}
            )
            activities[name] = activity
            self.log(f"{'Created' if created else 'Updated'} activity {name}")
        self.summary("Activity types", len(activities))
        return activities

    def seed_guides(self):
        guides = {}
        for data in GUIDES:
            user = self.get_or_create_user(data["email"], data["first_name"], data["last_name"], User.Role.GUIDE)
            GuideProfile.objects.update_or_create(
                user=user,
                defaults={
                    "bio": data["bio"],
                    "languages": data["languages"],
                    "years_of_experience": data["years_of_experience"],
                    "base_location": self.locations[data["base_location"]],
                },
            )
            guides[data["first_name"]] = user
        self.summary("Guides", len(guides))
        return guides

    def seed_customers(self):
        customers = {}
        for data in CUSTOMERS:
            user = self.get_or_create_user(data["email"], data["first_name"], data["last_name"], User.Role.CUSTOMER)
            customers[data["first_name"]] = user
        self.summary("Customers", len(customers))
        return customers