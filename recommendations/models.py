from django.db import models
from django.conf import settings
from movies.models import Movie, TVShow

class DailyPick(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_id = models.CharField(max_length=20)  # TMDB ID
    content_type = models.CharField(max_length=10)  # 'movie' or 'tv'
    score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'content_id', 'content_type')
    
    def __str__(self):
        return f"{self.user.email} - {self.content_type} - Score: {self.score}"

class WeeklySuggestion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_id = models.CharField(max_length=20)  # TMDB ID
    content_type = models.CharField(max_length=10)  # 'movie' or 'tv'
    score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'content_id', 'content_type')
    
    def __str__(self):
        return f"{self.user.email} - {self.content_type} - Score: {self.score}"

class GenreRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    genre_id = models.IntegerField()
    genre_name = models.CharField(max_length=50)
    score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.genre_name} - Score: {self.score}"