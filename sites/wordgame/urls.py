from django.urls import path
from django.conf.urls import include, url
from . import views

urlpatterns = [
    #game views
    path('', views.index, name='index'),
    path('custom/', views.custom, name='custom'),
    path('current/', views.current_headline, name='current'),
    path('local/', views.local_headline, name='local'),
    #new session vote screen
    path('new/', views.newsession, name='new'),
    #new init vote post
    path('init/', views.initialvote, name='init'),
    #vote post
    path('vote/', views.vote, name='vote'),
    #audio speech recognition handler
    path('audio/', views.audio, name='audio'),
    #text to speech handler
    path('tts/', views.tts, name='tts'),

    #other views
    path('creations/',views.creations, name='creations'),
    path('creationvote/',views.creationvote, name='creationvote'),
    path('creationdelete/',views.creationdelete, name='creationdelete')

]

urlpatterns += [
    url(r"^accounts/", include("django.contrib.auth.urls")),
    url(r"^dashboard/", views.dashboard, name="dashboard"),
    url(r"^register/", views.register, name="register"),
]

