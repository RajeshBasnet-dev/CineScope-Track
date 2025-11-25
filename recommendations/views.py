from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import DailyPick, WeeklySuggestion, GenreRecommendation, ContentBasedRecommendation, CollaborativeRecommendation
from movies.models import UserRating, Movie, TVShow
from watchlists.models import UserWatchlist
from services.tmdb_service import TMDBService
import random
from collections import defaultdict
import math

@login_required
def recommendations(request):
    """Display user's recommendations"""
    # Get existing recommendations
    daily_picks = DailyPick.objects.filter(user=request.user)
    weekly_suggestions = WeeklySuggestion.objects.filter(user=request.user)
    genre_recommendations = GenreRecommendation.objects.filter(user=request.user)
    content_based = ContentBasedRecommendation.objects.filter(user=request.user).order_by('-similarity_score')[:10]
    collaborative = CollaborativeRecommendation.objects.filter(user=request.user).order_by('-predicted_rating')[:10]
    
    # Enrich recommendations with real data
    tmdb_service = TMDBService()
    
    # Enrich daily picks
    enriched_daily_picks = []
    for pick in daily_picks:
        try:
            if pick.content_type == 'movie':
                details = tmdb_service.get_movie_details(pick.content_id)
                pick.title = details.get('title', 'Unknown Movie')
                pick.poster_path = details.get('poster_path', '')
                pick.overview = details.get('overview', '')
                pick.rating = details.get('vote_average', 0)
                enriched_daily_picks.append(pick)
            else:
                details = tmdb_service.get_tv_show_details(pick.content_id)
                pick.title = details.get('name', 'Unknown TV Show')
                pick.poster_path = details.get('poster_path', '')
                pick.overview = details.get('overview', '')
                pick.rating = details.get('vote_average', 0)
                enriched_daily_picks.append(pick)
        except Exception as e:
            # If we can't fetch details, skip this item
            pass
    
    # Enrich content-based recommendations
    enriched_content_based = []
    for rec in content_based:
        try:
            if rec.content_type == 'movie':
                details = tmdb_service.get_movie_details(rec.content_id)
                rec.title = details.get('title', 'Unknown Movie')
                rec.poster_path = details.get('poster_path', '')
                rec.overview = details.get('overview', '')
                rec.rating = details.get('vote_average', 0)
                enriched_content_based.append(rec)
            else:
                details = tmdb_service.get_tv_show_details(rec.content_id)
                rec.title = details.get('name', 'Unknown TV Show')
                rec.poster_path = details.get('poster_path', '')
                rec.overview = details.get('overview', '')
                rec.rating = details.get('vote_average', 0)
                enriched_content_based.append(rec)
        except Exception as e:
            # If we can't fetch details, skip this item
            pass
    
    context = {
        'daily_picks': enriched_daily_picks,
        'weekly_suggestions': weekly_suggestions,
        'genre_recommendations': genre_recommendations,
        'content_based': enriched_content_based,
        'collaborative': collaborative,
    }
    
    return render(request, 'recommendations/recommendations.html', context)

@login_required
def generate_recommendations(request):
    """Generate new recommendations for the user using real algorithms"""
    if request.method == 'POST':
        tmdb_service = TMDBService()
        user = request.user
        
        # Clear existing recommendations
        DailyPick.objects.filter(user=user).delete()
        WeeklySuggestion.objects.filter(user=user).delete()
        GenreRecommendation.objects.filter(user=user).delete()
        ContentBasedRecommendation.objects.filter(user=user).delete()
        CollaborativeRecommendation.objects.filter(user=user).delete()
        
        # Get user's ratings and watch history
        user_ratings = UserRating.objects.filter(user=user)
        watched_content = UserWatchlist.objects.filter(user=user, status='completed')
        
        # Generate content-based recommendations
        generate_content_based_recommendations(user, user_ratings, watched_content, tmdb_service)
        
        # Generate collaborative recommendations (simplified)
        generate_collaborative_recommendations(user, user_ratings, tmdb_service)
        
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
                score = item.get('vote_average', 0) * 10  # Convert to 0-100 scale
                
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
                score = item.get('popularity', 0)  # Use popularity as score
                
                WeeklySuggestion.objects.create(
                    user=user,
                    content_id=item['id'],
                    content_type=content_type,
                    score=score
                )
        except Exception as e:
            pass  # Handle API errors gracefully
        
        # Generate genre recommendations based on user ratings
        generate_genre_recommendations(user, user_ratings, tmdb_service)
        
        return JsonResponse({'success': True, 'message': 'Recommendations generated successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def generate_content_based_recommendations(user, user_ratings, watched_content, tmdb_service):
    """Generate content-based recommendations using user's preferences"""
    # Get user's favorite genres and highly rated content
    favorite_genres = defaultdict(int)
    favorite_directors = defaultdict(int)
    favorite_actors = defaultdict(int)
    
    # Analyze user ratings
    for rating in user_ratings:
        if rating.rating >= 7:  # Only consider ratings 7+ stars
            try:
                if rating.content_type == 'movie':
                    details = tmdb_service.get_movie_details(rating.content_id)
                    credits = tmdb_service.get_movie_credits(rating.content_id)
                else:
                    details = tmdb_service.get_tv_show_details(rating.content_id)
                    credits = tmdb_service.get_tv_show_credits(rating.content_id)
                
                # Extract genres
                for genre in details.get('genres', []):
                    favorite_genres[genre['id']] += rating.rating
                
                # Extract directors (for movies)
                if rating.content_type == 'movie':
                    for crew_member in credits.get('crew', []):
                        if crew_member.get('job') == 'Director':
                            favorite_directors[crew_member['id']] += rating.rating
                
                # Extract top actors
                for cast_member in credits.get('cast', [])[:5]:  # Top 5 actors
                    favorite_actors[cast_member['id']] += rating.rating
                    
            except Exception as e:
                # Skip if we can't fetch details
                pass
    
    # Get recommendations based on favorite genres
    if favorite_genres:
        # Sort genres by preference score
        sorted_genres = sorted(favorite_genres.items(), key=lambda x: x[1], reverse=True)
        top_genres = sorted_genres[:3]  # Top 3 genres
        
        # For each top genre, find popular content
        for genre_id, score in top_genres:
            try:
                # Discover movies with this genre
                params = {
                    'with_genres': genre_id,
                    'sort_by': 'popularity.desc',
                    'page': 1
                }
                
                genre_movies = tmdb_service._make_request('discover/movie', params)
                
                # Score and recommend top items
                for item in genre_movies.get('results', [])[:5]:
                    # Calculate similarity score based on user preference and item popularity
                    similarity_score = (score / 10.0) * (item.get('popularity', 0) / 100.0) * 100
                    
                    # Only recommend if score is high enough
                    if similarity_score > 20:
                        ContentBasedRecommendation.objects.create(
                            user=user,
                            content_id=item['id'],
                            content_type='movie',
                            similarity_score=similarity_score,
                            reason=f"Popular in genre you like"
                        )
            except Exception as e:
                pass

def generate_collaborative_recommendations(user, user_ratings, tmdb_service):
    """Generate collaborative recommendations (simplified)"""
    # In a real implementation, this would compare the user with similar users
    # For now, we'll use a simplified approach based on trending content
    try:
        # Get trending content that the user hasn't rated or watched
        trending_movies = tmdb_service.get_trending_movies()
        trending_tv = tmdb_service.get_trending_tv_shows()
        
        # Get user's rated content IDs
        rated_content_ids = set(rating.content_id for rating in user_ratings)
        watched_content_ids = set(watchlist.content_id for watchlist in UserWatchlist.objects.filter(user=user))
        all_user_content = rated_content_ids.union(watched_content_ids)
        
        # Recommend trending content the user hasn't seen
        all_trending = trending_movies.get('results', []) + trending_tv.get('results', [])
        
        for item in all_trending[:20]:  # Check top 20 trending items
            content_id = str(item['id'])
            if content_id not in all_user_content:
                content_type = 'movie' if 'title' in item else 'tv'
                predicted_rating = item.get('vote_average', 0) * 10  # Convert to 0-100 scale
                
                # Only recommend if rating is decent
                if predicted_rating >= 60:
                    CollaborativeRecommendation.objects.create(
                        user=user,
                        content_id=content_id,
                        content_type=content_type,
                        user_similarity_score=0.7,  # Placeholder
                        predicted_rating=predicted_rating
                    )
                    
                # Limit to 10 recommendations
                if CollaborativeRecommendation.objects.filter(user=user).count() >= 10:
                    break
    except Exception as e:
        pass

def generate_genre_recommendations(user, user_ratings, tmdb_service):
    """Generate genre recommendations based on user ratings"""
    # Get user's favorite genres from ratings
    favorite_genres = defaultdict(int)
    
    for rating in user_ratings:
        if rating.rating >= 6:  # Only consider ratings 6+ stars
            try:
                if rating.content_type == 'movie':
                    details = tmdb_service.get_movie_details(rating.content_id)
                else:
                    details = tmdb_service.get_tv_show_details(rating.content_id)
                
                # Extract genres
                for genre in details.get('genres', []):
                    favorite_genres[genre['id']] += 1
            except Exception as e:
                pass
    
    # Create genre recommendations
    genre_list = tmdb_service.get_movie_genres()
    genre_dict = {genre['id']: genre['name'] for genre in genre_list.get('genres', [])}
    
    for genre_id, count in list(favorite_genres.items())[:5]:
        genre_name = genre_dict.get(genre_id, f"Genre {genre_id}")
        GenreRecommendation.objects.create(
            user=user,
            genre_id=genre_id,
            genre_name=genre_name,
            score=count * 2.0
        )