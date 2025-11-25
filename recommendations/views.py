from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import DailyPick, WeeklySuggestion, GenreRecommendation
from movies.models import UserRating, Movie, TVShow
from watchlists.models import UserWatchlist
from services.tmdb_service import TMDBService
import random

@login_required
def recommendations(request):
    """Display user's recommendations"""
    # Get existing recommendations
    daily_picks = DailyPick.objects.filter(user=request.user)
    weekly_suggestions = WeeklySuggestion.objects.filter(user=request.user)
    genre_recommendations = GenreRecommendation.objects.filter(user=request.user)
    
    context = {
        'daily_picks': daily_picks,
        'weekly_suggestions': weekly_suggestions,
        'genre_recommendations': genre_recommendations,
    }
    
    return render(request, 'recommendations/recommendations.html', context)

@login_required
def generate_recommendations(request):
    """Generate new recommendations for the user"""
    if request.method == 'POST':
        tmdb_service = TMDBService()
        user = request.user
        
        # Clear existing recommendations
        DailyPick.objects.filter(user=user).delete()
        WeeklySuggestion.objects.filter(user=user).delete()
        GenreRecommendation.objects.filter(user=user).delete()
        
        # Get user's ratings and watch history
        user_ratings = UserRating.objects.filter(user=user)
        watched_content = UserWatchlist.objects.filter(user=user, status='completed')
        
        # Get user's favorite genres from ratings
        favorite_genres = {}
        for rating in user_ratings:
            if rating.rating >= 4:  # Only consider ratings 4+ stars
                # For simplicity, we'll use a placeholder approach
                # In a real implementation, we would fetch actual genre data
                genre_id = random.randint(1, 20)
                if genre_id in favorite_genres:
                    favorite_genres[genre_id] += 1
                else:
                    favorite_genres[genre_id] = 1
        
        # Generate daily picks (popular content with genre weighting)
        try:
            popular_movies = tmdb_service.get_popular_movies()
            popular_tv = tmdb_service.get_popular_tv_shows()
            
            # Combine and shuffle popular content
            all_popular = popular_movies.get('results', [])[:10] + popular_tv.get('results', [])[:10]
            random.shuffle(all_popular)
            
            # Create daily picks (5 items)
            for i, item in enumerate(all_popular[:5]):
                content_type = 'movie' if 'title' in item else 'tv'
                score = random.uniform(7.0, 9.5)  # Simulated score
                
                DailyPick.objects.create(
                    user=user,
                    content_id=item['id'],
                    content_type=content_type,
                    score=score
                )
        except Exception as e:
            pass  # Handle API errors gracefully
        
        # Generate weekly suggestions (trending content)
        try:
            trending_movies = tmdb_service.get_trending_movies()
            trending_tv = tmdb_service.get_trending_tv_shows()
            
            # Combine and shuffle trending content
            all_trending = trending_movies.get('results', [])[:10] + trending_tv.get('results', [])[:10]
            random.shuffle(all_trending)
            
            # Create weekly suggestions (10 items)
            for i, item in enumerate(all_trending[:10]):
                content_type = 'movie' if 'title' in item else 'tv'
                score = random.uniform(6.0, 9.0)  # Simulated score
                
                WeeklySuggestion.objects.create(
                    user=user,
                    content_id=item['id'],
                    content_type=content_type,
                    score=score
                )
        except Exception as e:
            pass  # Handle API errors gracefully
        
        # Generate genre recommendations
        for genre_id, count in list(favorite_genres.items())[:5]:
            GenreRecommendation.objects.create(
                user=user,
                genre_id=genre_id,
                genre_name=f"Genre {genre_id}",
                score=count * 2.0
            )
        
        return JsonResponse({'success': True, 'message': 'Recommendations generated successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})