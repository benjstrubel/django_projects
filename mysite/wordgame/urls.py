from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index, name='index')
    path('api/wordgame/', views.BlurbListCreate.as_view() ),
]

