from rest_framework import serializers
from .models import Blurb

class BlurbSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blurb
        fields = ('id','text')