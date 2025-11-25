from django.db import models
from django.conf import settings
from movies.models import Movie, TVShow

class UserAnalytics(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_hours_watched = models.FloatField(default=0)
    total_movies_watched = models.IntegerField(default=0)
    total_episodes_watched = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - Analytics"

class GenreTimeSpent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    genre_id = models.IntegerField()
    genre_name = models.CharField(max_length=50)
    hours_spent = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'genre_id')
    
    def __str__(self):
        return f"{self.user.email} - {self.genre_name} - {self.hours_spent} hours"

class MonthlyActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    hours_watched = models.FloatField(default=0)
    movies_watched = models.IntegerField(default=0)
    episodes_watched = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'year', 'month')
    
    def __str__(self):
        return f"{self.user.email} - {self.year}-{self.month}: {self.hours_watched} hours"