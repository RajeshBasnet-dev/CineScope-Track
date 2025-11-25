from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='movies_home'),
    path('search/', views.search, name='search'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('tv/<int:tv_id>/', views.tv_show_detail, name='tv_show_detail'),
    path('submit-rating/', views.submit_rating, name='submit_rating'),
    path('user-ratings/', views.get_user_ratings, name='user_ratings'),
    path('write-review/<str:content_type>/<int:content_id>/', views.write_review, name='write_review'),
]