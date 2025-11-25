from django.db import models
from django.conf import settings
from movies.models import Movie, TVShow

class UserWatchlist(models.Model):
    WATCHLIST_STATUS_CHOICES = [
        ('plan_to_watch', 'Plan to Watch'),
        ('watching', 'Watching'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_id = models.CharField(max_length=20)  # TMDB ID
    content_type = models.CharField(max_length=10)  # 'movie' or 'tv'
    status = models.CharField(max_length=20, choices=WATCHLIST_STATUS_CHOICES, default='plan_to_watch')
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'content_id', 'content_type')
    
    def __str__(self):
        return f"{self.user.email} - {self.content_type} - {self.status}"

class CustomList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"

class CustomListEntry(models.Model):
    custom_list = models.ForeignKey(CustomList, on_delete=models.CASCADE, related_name='entries')
    content_id = models.CharField(max_length=20)  # TMDB ID
    content_type = models.CharField(max_length=10)  # 'movie' or 'tv'
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.custom_list.name} - {self.content_type}"

class UserEpisodeProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE)
    season = models.IntegerField()
    episode = models.IntegerField()
    watched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'tv_show', 'season', 'episode')
    
    def __str__(self):
        return f"{self.user.email} - {self.tv_show.title} - S{self.season}E{self.episode}"