from django.contrib import admin
from .models import Blurb, ScoreVector, Creation, User

# Register your models here.
admin.site.register(Blurb)
admin.site.register(ScoreVector)
admin.site.register(Creation)
