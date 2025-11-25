from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserWatchlist, CustomList, CustomListEntry, UserEpisodeProgress
from movies.models import Movie, TVShow, Episode
import json

@login_required
def watchlist(request):
    """Display user's watchlists"""
    watchlists = UserWatchlist.objects.filter(user=request.user)
    
    # Group by status
    plan_to_watch = watchlists.filter(status='plan_to_watch')
    watching = watchlists.filter(status='watching')
    completed = watchlists.filter(status='completed')
    dropped = watchlists.filter(status='dropped')
    
    context = {
        'plan_to_watch': plan_to_watch,
        'watching': watching,
        'completed': completed,
        'dropped': dropped,
    }
    
    return render(request, 'watchlists/watchlist.html', context)

@login_required
def episode_tracker(request, tv_id):
    """Display episode tracker for a TV show"""
    # Get the TV show from TMDB
    from services.tmdb_service import TMDBService
    tmdb_service = TMDBService()
    
    try:
        tv_show = tmdb_service.get_tv_show_details(tv_id)
        # For simplicity, we'll simulate episodes
        episodes = []
        for season_num in range(1, min(tv_show.get('number_of_seasons', 1) + 1, 4)):  # Limit to 3 seasons
            season_data = tmdb_service.get_tv_season_details(tv_id, season_num)
            for ep in season_data.get('episodes', []):
                episodes.append({
                    'season_number': season_num,
                    'episode_number': ep['episode_number'],
                    'name': ep['name'],
                    'runtime': ep.get('runtime', 45),
                    'overview': ep.get('overview', ''),
                })
    except Exception as e:
        tv_show = None
        episodes = []
    
    # Get user's watched episodes
    watched_episodes = UserEpisodeProgress.objects.filter(
        user=request.user,
        tv_show__tmdb_id=tv_id
    )
    
    watched_episode_ids = [
        (progress.season, progress.episode) 
        for progress in watched_episodes
    ]
    
    context = {
        'tv_show': tv_show,
        'episodes': episodes,
        'watched_episode_ids': watched_episode_ids,
    }
    
    return render(request, 'watchlists/episode_tracker.html', context)

@login_required
def toggle_episode_watched(request):
    """Toggle episode watched status"""
    if request.method == 'POST':
        data = json.loads(request.body)
        tv_id = data.get('tv_id')
        season_number = data.get('season_number')
        episode_number = data.get('episode_number')
        
        try:
            # Get or create TV show in our database
            tv_show, created = TVShow.objects.get_or_create(
                tmdb_id=tv_id,
                defaults={
                    'title': f'TV Show {tv_id}',
                    'overview': '',
                    'type': 'tv'
                }
            )
            
            # Check if episode is already marked as watched
            try:
                progress = UserEpisodeProgress.objects.get(
                    user=request.user,
                    tv_show=tv_show,
                    season=season_number,
                    episode=episode_number
                )
                # Unmark as watched
                progress.delete()
                watched = False
            except UserEpisodeProgress.DoesNotExist:
                # Mark as watched
                UserEpisodeProgress.objects.create(
                    user=request.user,
                    tv_show=tv_show,
                    season=season_number,
                    episode=episode_number
                )
                watched = True
            
            return JsonResponse({
                'success': True, 
                'watched': watched,
                'message': 'Episode status updated'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': 'Error updating episode status'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def add_to_watchlist(request):
    """Add a movie or TV show to the user's watchlist"""
    if request.method == 'POST':
        data = json.loads(request.body)
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        status = data.get('status', 'plan_to_watch')
        
        # Check if already in watchlist
        watchlist_item, created = UserWatchlist.objects.get_or_create(
            user=request.user,
            content_id=content_id,
            content_type=content_type,
            defaults={'status': status}
        )
        
        if not created:
            watchlist_item.status = status
            watchlist_item.save()
        
        return JsonResponse({'success': True, 'message': 'Added to watchlist'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def move_watchlist_item(request):
    """Move a watchlist item to a different status"""
    if request.method == 'POST':
        data = json.loads(request.body)
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        new_status = data.get('new_status')
        
        try:
            watchlist_item = UserWatchlist.objects.get(
                user=request.user,
                content_id=content_id,
                content_type=content_type
            )
            watchlist_item.status = new_status
            watchlist_item.save()
            
            return JsonResponse({'success': True, 'message': 'Item moved successfully'})
        except UserWatchlist.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Item not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def remove_from_watchlist(request):
    """Remove an item from the user's watchlist"""
    if request.method == 'POST':
        data = json.loads(request.body)
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        
        try:
            watchlist_item = UserWatchlist.objects.get(
                user=request.user,
                content_id=content_id,
                content_type=content_type
            )
            watchlist_item.delete()
            
            return JsonResponse({'success': True, 'message': 'Item removed successfully'})
        except UserWatchlist.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Item not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})