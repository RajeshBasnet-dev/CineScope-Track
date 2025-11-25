from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from services.tmdb_service import TMDBService
from .models import UserRating
import json

def home(request):
    """Home page with trending content"""
    tmdb_service = TMDBService()
    
    # Get trending movies and TV shows
    try:
        trending_movies = tmdb_service.get_trending_movies()
        trending_tv = tmdb_service.get_trending_tv_shows()
        
        context = {
            'trending_movies': trending_movies.get('results', [])[:6],
            'trending_tv': trending_tv.get('results', [])[:6],
        }
    except Exception as e:
        context = {
            'trending_movies': [],
            'trending_tv': [],
        }
    
    return render(request, 'movies/home.html', context)

def search(request):
    """Search movies and TV shows"""
    query = request.GET.get('q', '')
    tmdb_service = TMDBService()
    
    if query:
        try:
            movies = tmdb_service.search_movies(query)
            tv_shows = tmdb_service.search_tv_shows(query)
            
            context = {
                'query': query,
                'movies': movies.get('results', []),
                'tv_shows': tv_shows.get('results', []),
            }
        except Exception as e:
            context = {
                'query': query,
                'movies': [],
                'tv_shows': [],
            }
    else:
        context = {
            'query': '',
            'movies': [],
            'tv_shows': [],
        }
    
    return render(request, 'movies/search.html', context)

def movie_detail(request, movie_id):
    """Display movie details"""
    tmdb_service = TMDBService()
    
    try:
        movie = tmdb_service.get_movie_details(movie_id)
        credits = tmdb_service.get_movie_credits(movie_id)
        
        # Get user's rating if logged in
        user_rating = None
        user_review = None
        user_watch_status = None
        
        if request.user.is_authenticated:
            try:
                rating_obj = UserRating.objects.get(
                    user=request.user,
                    content_id=movie_id,
                    content_type='movie'
                )
                user_rating = rating_obj.rating
                user_review = rating_obj.review_text
            except UserRating.DoesNotExist:
                pass
            
            # Get user's watch status
            try:
                from watchlists.models import UserWatchlist
                watchlist_item = UserWatchlist.objects.get(
                    user=request.user,
                    content_id=movie_id,
                    content_type='movie'
                )
                user_watch_status = watchlist_item.status
            except UserWatchlist.DoesNotExist:
                user_watch_status = None
        
        context = {
            'movie': movie,
            'cast': credits.get('cast', [])[:15],
            'crew': credits.get('crew', [])[:15],
            'user_rating': user_rating,
            'user_review': user_review,
            'user_watch_status': user_watch_status,
        }
    except Exception as e:
        context = {
            'movie': None,
        }
    
    return render(request, 'movies/movie_detail.html', context)

def tv_show_detail(request, tv_id):
    """Display TV show details"""
    tmdb_service = TMDBService()
    
    try:
        tv_show = tmdb_service.get_tv_show_details(tv_id)
        credits = tmdb_service.get_tv_show_credits(tv_id)
        
        # Get user's rating if logged in
        user_rating = None
        if request.user.is_authenticated:
            try:
                rating_obj = UserRating.objects.get(
                    user=request.user,
                    content_id=tv_id,
                    content_type='tv'
                )
                user_rating = rating_obj.rating
            except UserRating.DoesNotExist:
                pass
        
        context = {
            'tv_show': tv_show,
            'cast': credits.get('cast', [])[:10],
            'crew': credits.get('crew', [])[:10],
            'user_rating': user_rating,
        }
    except Exception as e:
        context = {
            'tv_show': None,
        }
    
    return render(request, 'movies/tv_show_detail.html', context)

@login_required
def write_review(request, content_type, content_id):
    """Display write review page"""
    tmdb_service = TMDBService()
    
    try:
        if content_type == 'movie':
            content = tmdb_service.get_movie_details(content_id)
        elif content_type == 'tv':
            content = tmdb_service.get_tv_show_details(content_id)
        else:
            content = None
        
        # Get user's existing rating if it exists
        user_rating = None
        review_title = ""
        review_text = ""
        
        if request.user.is_authenticated:
            try:
                rating_obj = UserRating.objects.get(
                    user=request.user,
                    content_id=content_id,
                    content_type=content_type
                )
                user_rating = rating_obj.rating
                review_title = rating_obj.review_title or ""
                review_text = rating_obj.review_text or ""
            except UserRating.DoesNotExist:
                pass
        
        context = {
            'content': content,
            'content_type': content_type,
            'content_id': content_id,
            'user_rating': user_rating,
            'review_title': review_title,
            'review_text': review_text,
        }
    except Exception as e:
        context = {
            'content': None,
            'content_type': content_type,
            'content_id': content_id,
        }
    
    return render(request, 'movies/write_review.html', context)

@login_required
def submit_rating(request):
    """Submit or update a user rating"""
    if request.method == 'POST':
        data = json.loads(request.body)
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        rating = data.get('rating')
        review_title = data.get('review_title', '')
        review_text = data.get('review_text', '')
        contains_spoilers = data.get('contains_spoilers', False)
        
        try:
            # Create or update rating
            rating_obj, created = UserRating.objects.update_or_create(
                user=request.user,
                content_id=content_id,
                content_type=content_type,
                defaults={
                    'rating': rating,
                    'review_title': review_title,
                    'review_text': review_text,
                    'contains_spoilers': contains_spoilers
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Rating submitted successfully',
                'created': created
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error submitting rating'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def get_user_ratings(request):
    """Get user's ratings"""
    if request.method == 'GET':
        ratings = UserRating.objects.filter(user=request.user)
        ratings_data = []
        
        for rating in ratings:
            ratings_data.append({
                'content_id': rating.content_id,
                'content_type': rating.content_type,
                'rating': rating.rating,
                'review_title': rating.review_title,
                'review_text': rating.review_text,
                'contains_spoilers': rating.contains_spoilers,
                'created_at': rating.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'ratings': ratings_data
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})