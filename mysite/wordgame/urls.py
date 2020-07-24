from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('new/', views.newsession, name='new'),
    path('init/', views.initialvote, name='init'),
    path('vote/', views.vote, name='vote')
]

