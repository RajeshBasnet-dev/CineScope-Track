from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserAnalytics, GenreTimeSpent, MonthlyActivity
from movies.models import UserRating
from watchlists.models import UserWatchlist, UserEpisodeProgress
from django.db.models import Count, Sum, Avg
from datetime import datetime, timedelta
import json

@login_required
def dashboard(request):
    """Display user's analytics dashboard"""
    user = request.user
    
    # Get or create user analytics
    user_analytics, created = UserAnalytics.objects.get_or_create(user=user)
    
    # Update analytics data
    update_user_analytics(user)
    
    # Refresh the object after update
    user_analytics.refresh_from_db()
    
    # Get genre time spent data
    genre_data = GenreTimeSpent.objects.filter(user=user).order_by('-hours_spent')[:5]
    
    # Get monthly activity data (last 12 months)
    monthly_data = MonthlyActivity.objects.filter(user=user).order_by('-year', '-month')[:12]
    
    # Get user ratings with aggregation
    user_ratings = UserRating.objects.filter(user=user)
    ratings_aggregate = user_ratings.aggregate(
        count=Count('rating'),
        sum=Sum('rating'),
        average=Avg('rating')
    )
    
    # Get completion rate
    total_watchlist_items = UserWatchlist.objects.filter(user=user).count()
    completed_items = UserWatchlist.objects.filter(user=user, status='completed').count()
    completion_rate = (completed_items / total_watchlist_items * 100) if total_watchlist_items > 0 else 0
    
    # Prepare data for charts
    # Monthly activity data for the chart
    monthly_labels = []
    monthly_hours = []
    monthly_movies = []
    monthly_episodes = []
    
    # Process monthly data in reverse order (oldest first for chart)
    for activity in reversed(list(monthly_data)):
        month_name = datetime(2000, activity.month, 1).strftime('%b')
        monthly_labels.append(month_name)
        monthly_hours.append(activity.hours_watched)
        monthly_movies.append(activity.movies_watched)
        monthly_episodes.append(activity.episodes_watched)
    
    # Genre data for the chart
    genre_labels = []
    genre_hours = []
    
    for genre in genre_data:
        genre_labels.append(genre.genre_name)
        genre_hours.append(genre.hours_spent)
    
    # Rating distribution data
    ratings_data = {}
    for i in range(1, 11):
        ratings_data[i] = UserRating.objects.filter(user=user, rating=i).count()
    
    context = {
        'user_analytics': user_analytics,
        'genre_data': genre_data,
        'monthly_data': monthly_data,
        'user_ratings': user_ratings,
        'ratings_aggregate': ratings_aggregate,
        'completion_rate': completion_rate,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_hours': json.dumps(monthly_hours),
        'monthly_movies': json.dumps(monthly_movies),
        'monthly_episodes': json.dumps(monthly_episodes),
        'genre_labels': json.dumps(genre_labels),
        'genre_hours': json.dumps(genre_hours),
        'ratings_data': json.dumps(ratings_data)
    }
    
    return render(request, 'analytics/dashboard.html', context)

def update_user_analytics(user):
    """Update user analytics data"""
    try:
        user_analytics, created = UserAnalytics.objects.get_or_create(user=user)
        
        # Update total movies watched
        movies_watched = UserWatchlist.objects.filter(
            user=user, 
            content_type='movie', 
            status='completed'
        ).count()
        user_analytics.total_movies_watched = movies_watched
        
        # Update total episodes watched
        episodes_watched = UserEpisodeProgress.objects.filter(user=user).count()
        user_analytics.total_episodes_watched = episodes_watched
        
        # Calculate total hours watched (estimate)
        # Assume average movie length of 120 minutes and average episode length of 45 minutes
        total_hours = (movies_watched * 2) + (episodes_watched * 0.75)
        user_analytics.total_hours_watched = total_hours
        
        user_analytics.save()
        
        # Update monthly activity (simplified - just current month)
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        monthly_activity, created = MonthlyActivity.objects.get_or_create(
            user=user,
            year=current_year,
            month=current_month,
            defaults={
                'hours_watched': 0,
                'movies_watched': 0,
                'episodes_watched': 0
            }
        )
        
        # Update monthly stats
        monthly_activity.movies_watched = UserWatchlist.objects.filter(
            user=user,
            content_type='movie',
            status='completed'
        ).count()
        
        monthly_activity.episodes_watched = UserEpisodeProgress.objects.filter(
            user=user
        ).count()
        
        # Estimate hours watched this month
        monthly_activity.hours_watched = (
            monthly_activity.movies_watched * 2 + 
            monthly_activity.episodes_watched * 0.75
        )
        
        monthly_activity.save()
        
        # Update genre time spent (simplified)
        # In a real implementation, we would fetch actual genre data from TMDB
        # For now, we'll create some sample data
        GenreTimeSpent.objects.update_or_create(
            user=user,
            genre_id=28,
            defaults={
                'genre_name': 'Action',
                'hours_spent': total_hours * 0.25
            }
        )
        
        GenreTimeSpent.objects.update_or_create(
            user=user,
            genre_id=12,
            defaults={
                'genre_name': 'Adventure',
                'hours_spent': total_hours * 0.20
            }
        )
        
        GenreTimeSpent.objects.update_or_create(
            user=user,
            genre_id=16,
            defaults={
                'genre_name': 'Animation',
                'hours_spent': total_hours * 0.10
            }
        )
        
        GenreTimeSpent.objects.update_or_create(
            user=user,
            genre_id=35,
            defaults={
                'genre_name': 'Comedy',
                'hours_spent': total_hours * 0.15
            }
        )
        
        GenreTimeSpent.objects.update_or_create(
            user=user,
            genre_id=80,
            defaults={
                'genre_name': 'Crime',
                'hours_spent': total_hours * 0.10
            }
        )
        
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error updating analytics for user {user.id}: {e}")
        pass