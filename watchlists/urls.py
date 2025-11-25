from django.urls import path
from . import views

urlpatterns = [
    path('', views.watchlist, name='watchlist'),
    path('episode-tracker/<int:tv_id>/', views.episode_tracker, name='episode_tracker'),
    path('toggle-episode/', views.toggle_episode_watched, name='toggle_episode_watched'),
    path('add/', views.add_to_watchlist, name='add_to_watchlist'),
    path('move/', views.move_watchlist_item, name='move_watchlist_item'),
    path('remove/', views.remove_from_watchlist, name='remove_from_watchlist'),
]