from django.contrib import admin
from .models import Blurb, ScoreVectorNew, Creation, User,PreferenceVector

# Register your models here.
admin.site.register(Blurb)
#admin.site.register(ScoreVector)
admin.site.register(Creation)
admin.site.register(ScoreVectorNew)
admin.site.register(PreferenceVector)