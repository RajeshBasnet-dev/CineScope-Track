import requests
import os
import json
import hashlib
from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import now
from datetime import timedelta

# TMDB API Configuration
TMDB_API_KEY = "c59cd50baf625458f0a1018e6d694d16"
TMDB_READ_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjNTljZDUwYmFmNjI1NDU4ZjBhMTAxOGU2ZDY5NGQxNiIsIm5iZiI6MTc2MjM0MDA0OC4xMDUsInN1YiI6IjY5MGIyY2QwZmQwN2FiYjVhYTYxM2EzNyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.5C2G_u78ThB_T6MfmMOpPfdSjmczTqvS_lBVA_GT6z0"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

class TMDBService:
    def __init__(self):
        self.api_key = TMDB_API_KEY
        self.read_access_token = TMDB_READ_ACCESS_TOKEN
        self.base_url = TMDB_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.read_access_token}",
            "Content-Type": "application/json;charset=utf-8"
        }
        # Cache timeout: 1 hour for most data, 24 hours for static data
        self.default_cache_timeout = 3600
        self.long_cache_timeout = 86400

    def _generate_cache_key(self, endpoint, params=None):
        """Generate a cache key for the request"""
        key_string = f"{endpoint}"
        if params:
            # Sort params to ensure consistent key generation
            sorted_params = sorted(params.items())
            key_string += f"?{sorted_params}"
        return f"tmdb_{hashlib.md5(key_string.encode()).hexdigest()}"

    def _get_from_cache(self, cache_key):
        """Get data from cache"""
        return cache.get(cache_key)

    def _set_in_cache(self, cache_key, data, timeout=None):
        """Set data in cache"""
        if timeout is None:
            timeout = self.default_cache_timeout
        cache.set(cache_key, data, timeout)

    def _make_request(self, endpoint, params=None):
        """Make a request to TMDB API with caching"""
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        
        # Generate cache key
        cache_key = self._generate_cache_key(endpoint, params)
        
        # Try to get from cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Make actual request if not in cache
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # Cache the response
            self._set_in_cache(cache_key, data)
            return data
        else:
            response.raise_for_status()

    def search_movies(self, query, page=1):
        """Search for movies"""
        params = {
            'query': query,
            'page': page
        }
        return self._make_request('search/movie', params)

    def search_tv_shows(self, query, page=1):
        """Search for TV shows"""
        params = {
            'query': query,
            'page': page
        }
        return self._make_request('search/tv', params)

    def get_movie_details(self, movie_id):
        """Get detailed information about a movie"""
        return self._make_request(f'movie/{movie_id}')

    def get_tv_show_details(self, tv_id):
        """Get detailed information about a TV show"""
        return self._make_request(f'tv/{tv_id}')

    def get_movie_credits(self, movie_id):
        """Get cast and crew for a movie"""
        # Longer cache timeout for credits as they rarely change
        cache_key = self._generate_cache_key(f'movie/{movie_id}/credits')
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        data = self._make_request(f'movie/{movie_id}/credits')
        self._set_in_cache(cache_key, data, self.long_cache_timeout)
        return data

    def get_tv_show_credits(self, tv_id):
        """Get cast and crew for a TV show"""
        # Longer cache timeout for credits as they rarely change
        cache_key = self._generate_cache_key(f'tv/{tv_id}/credits')
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        data = self._make_request(f'tv/{tv_id}/credits')
        self._set_in_cache(cache_key, data, self.long_cache_timeout)
        return data

    def get_trending_movies(self, time_window='week'):
        """Get trending movies"""
        return self._make_request(f'trending/movie/{time_window}')

    def get_trending_tv_shows(self, time_window='week'):
        """Get trending TV shows"""
        return self._make_request(f'trending/tv/{time_window}')

    def get_popular_movies(self, page=1):
        """Get popular movies"""
        params = {'page': page}
        return self._make_request('movie/popular', params)

    def get_popular_tv_shows(self, page=1):
        """Get popular TV shows"""
        params = {'page': page}
        return self._make_request('tv/popular', params)

    def get_top_rated_movies(self, page=1):
        """Get top rated movies"""
        params = {'page': page}
        return self._make_request('movie/top_rated', params)

    def get_top_rated_tv_shows(self, page=1):
        """Get top rated TV shows"""
        params = {'page': page}
        return self._make_request('tv/top_rated', params)

    def get_movie_genres(self):
        """Get movie genres"""
        # Longer cache timeout for genres as they rarely change
        cache_key = self._generate_cache_key('genre/movie/list')
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        data = self._make_request('genre/movie/list')
        self._set_in_cache(cache_key, data, self.long_cache_timeout)
        return data

    def get_tv_genres(self):
        """Get TV show genres"""
        # Longer cache timeout for genres as they rarely change
        cache_key = self._generate_cache_key('genre/tv/list')
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        data = self._make_request('genre/tv/list')
        self._set_in_cache(cache_key, data, self.long_cache_timeout)
        return data

    def get_tv_season_details(self, tv_id, season_number):
        """Get details for a specific TV season"""
        return self._make_request(f'tv/{tv_id}/season/{season_number}')