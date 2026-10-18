# convert django models to JSON
# like a DTO in ASP.NET which fields will be shown etc 
# DRF ModelSerializer 
from rest_framework import serializers
from .models import Tour,TourSlot
from django.utils import timezone

class TourSerializer(serializers.ModelSerializer):
    guide=serializers.CharField(source="guide.get_full_name",read_only=True)
    activity_type=serializers.CharField(source="activity_type.name",read_only=True)
    location = serializers.CharField(source="location.name", read_only=True)
    average_rating = serializers.DecimalField(
        max_digits=3, decimal_places=1, coerce_to_string=False, read_only=True
    )
    review_count = serializers.IntegerField(read_only=True)


    #models and fields in JSON 
    class Meta:
        model=Tour
        fields=[
            "id",
            "title",
            "description",
            "guide",
            "activity_type",
            "location",
            "duration_minutes",
            "difficulty",
            "price",
            "max_participants",
            "average_rating",
            "review_count",

        ]

#tour slot serializer convert a slot to JSON 
class TourSlotSerializer(serializers.ModelSerializer):
    available_spots=serializers.IntegerField(read_only=True)
    class Meta:
        model=TourSlot
        fields=["id","start_time","available_spots"]

#tour details serializer 
class TourDetailSerializer(TourSerializer):
    slots=TourSlotSerializer(many=True,read_only=True)
    class Meta(TourSerializer.Meta):
        fields=TourSerializer.Meta.fields+["slots"]


#Guide tour serializer 
class GuideTourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tour
        fields = [
            "id",
            "title",
            "description",
            "activity_type",
            "location",
            "duration_minutes",
            "difficulty",
            "price",
            "max_participants",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {
            "duration_minutes": {"min_value": 1},
            "max_participants": {"min_value": 1},
            "price": {"min_value": 0},
        }

    def validate_max_participants(self, value):
        if self.instance is not None:
            most_booked = max(
                (slot.booked_spots for slot in self.instance.slots.all()), default=0
            )
            if value < most_booked:
                raise serializers.ValidationError(
                    f"Cannot be lower than {most_booked}, the most booked spots on a slot."
                )
        return value

    
class GuideTourSlotSerializer(TourSlotSerializer):
    def validate_start_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Slots must be scheduled in the future.")
        return value