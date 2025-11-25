from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserWatchlist, CustomList, CustomListEntry, UserEpisodeProgress
from movies.models import Movie, TVShow, Episode
import json

@login_required
def watchlist(request):
    """Display user's watchlists with real data from TMDB"""
    from services.tmdb_service import TMDBService
    tmdb_service = TMDBService()
    
    try:
        watchlists = UserWatchlist.objects.filter(user=request.user)
        
        # Group by status
        plan_to_watch = watchlists.filter(status='plan_to_watch')
        watching = watchlists.filter(status='watching')
        completed = watchlists.filter(status='completed')
        dropped = watchlists.filter(status='dropped')
        
        # Fetch real data for each watchlist item
        def enrich_watchlist_items(items):
            enriched_items = []
            for item in items:
                try:
                    if item.content_type == 'movie':
                        details = tmdb_service.get_movie_details(item.content_id)
                        item.title = details.get('title', 'Unknown Movie')
                        item.poster_path = details.get('poster_path', '')
                        item.release_date = details.get('release_date', '')
                    elif item.content_type == 'tv':
                        details = tmdb_service.get_tv_show_details(item.content_id)
                        item.title = details.get('name', 'Unknown TV Show')
                        item.poster_path = details.get('poster_path', '')
                        item.release_date = details.get('first_air_date', '')
                    enriched_items.append(item)
                except Exception as e:
                    # If we can't fetch details, use fallback data
                    item.title = 'Unknown Title'
                    item.poster_path = ''
                    item.release_date = ''
                    enriched_items.append(item)
            return enriched_items
        
        # Enrich all watchlist items with real data
        enriched_plan_to_watch = enrich_watchlist_items(plan_to_watch)
        enriched_watching = enrich_watchlist_items(watching)
        enriched_completed = enrich_watchlist_items(completed)
        enriched_dropped = enrich_watchlist_items(dropped)
        
        context = {
            'plan_to_watch': enriched_plan_to_watch,
            'watching': enriched_watching,
            'completed': enriched_completed,
            'dropped': enriched_dropped,
        }
    except Exception as e:
        # Handle any errors gracefully
        context = {
            'plan_to_watch': [],
            'watching': [],
            'completed': [],
            'dropped': [],
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

@login_required
def get_custom_lists(request):
    """Get all custom lists for the current user with entry details"""
    if request.method == 'GET':
        from services.tmdb_service import TMDBService
        tmdb_service = TMDBService()
        
        try:
            custom_lists = CustomList.objects.filter(user=request.user)
            lists_data = []
            
            for lst in custom_lists:
                # Get entries for this list
                entries = lst.entries.all()
                enriched_entries = []
                
                # Enrich each entry with real data
                for entry in entries:
                    try:
                        if entry.content_type == 'movie':
                            details = tmdb_service.get_movie_details(entry.content_id)
                            entry.title = details.get('title', 'Unknown Movie')
                            entry.poster_path = details.get('poster_path', '')
                            entry.release_date = details.get('release_date', '')
                        elif entry.content_type == 'tv':
                            details = tmdb_service.get_tv_show_details(entry.content_id)
                            entry.title = details.get('name', 'Unknown TV Show')
                            entry.poster_path = details.get('poster_path', '')
                            entry.release_date = details.get('first_air_date', '')
                        enriched_entries.append(entry)
                    except Exception as e:
                        # If we can't fetch details, use fallback data
                        entry.title = 'Unknown Title'
                        entry.poster_path = ''
                        entry.release_date = ''
                        enriched_entries.append(entry)
                
                lists_data.append({
                    'id': lst.id,
                    'name': lst.name,
                    'description': lst.description,
                    'entry_count': len(enriched_entries),
                    'entries': enriched_entries
                })
            
            return JsonResponse({
                'success': True,
                'lists': lists_data
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error retrieving custom lists'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
