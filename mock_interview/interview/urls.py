from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),                              # Home page
    path('resume_upload/', views.resume_upload, name='resume_upload'),  # Resume upload page
    path('live_stream/', views.live_stream, name='live_stream'),       # Mock interview live stream
    path('video_feed/', views.video_feed, name='video_feed'),           # Real-time video feed
    path('toggle_recording/', views.toggle_recording, name='toggle_recording'),  # Start/stop recording
]
