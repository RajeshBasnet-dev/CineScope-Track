from django.urls import path
from . import views

urlpatterns = [
    path('', views.recommendations, name='recommendations'),
    path('generate/', views.generate_recommendations, name='generate_recommendations'),
]