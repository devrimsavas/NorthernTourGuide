# convert django models to JSON
# like an DTO in ASP.NET which fields will be shown etc 
# DRF ModelSerializer 
from rest_framework import serializers
from .models import Tour,TourSlot

class TourSerializer(serializers.ModelSerializer):
    guide=serializers.CharField(source="guide.get_full_name",read_only=True)
    activity_type=serializers.CharField(source="activity_type.name",read_only=True)
    location = serializers.CharField(source="location.name", read_only=True)

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