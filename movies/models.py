from django.db import models
from django.conf import settings

class Movie(models.Model):
    tmdb_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    overview = models.TextField()
    poster_path = models.CharField(max_length=200, blank=True, null=True)
    runtime = models.IntegerField(blank=True, null=True)
    genres = models.JSONField(default=list)  # Store as list of genre IDs
    popularity = models.FloatField(default=0)
    type = models.CharField(max_length=10, default='movie')
    cached_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class TVShow(models.Model):
    tmdb_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    overview = models.TextField()
    poster_path = models.CharField(max_length=200, blank=True, null=True)
    genres = models.JSONField(default=list)  # Store as list of genre IDs
    popularity = models.FloatField(default=0)
    type = models.CharField(max_length=10, default='tv')
    total_seasons = models.IntegerField(default=0)
    cached_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Episode(models.Model):
    tmdb_id = models.CharField(max_length=20, unique=True)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name='episodes')
    season_number = models.IntegerField()
    episode_number = models.IntegerField()
    runtime = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.tv_show.title} - S{self.season_number}E{self.episode_number}: {self.name}"

class UserRating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_id = models.CharField(max_length=20)  # TMDB ID
    content_type = models.CharField(max_length=10)  # 'movie' or 'tv'
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 11)])  # 1-10 stars
    review_title = models.CharField(max_length=200, blank=True)
    review_text = models.TextField(blank=True)
    contains_spoilers = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'content_id', 'content_type')
    
    def __str__(self):
        return f"{self.user.email} - {self.content_type} - {self.rating} stars"