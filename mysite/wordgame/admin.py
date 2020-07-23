from django.contrib import admin
from .models import Blurb
from .models import ScoreVector

# Register your models here.
admin.site.register(Blurb)
admin.site.register(ScoreVector)
