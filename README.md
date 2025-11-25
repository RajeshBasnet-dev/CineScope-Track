# CineScope Tracker

A personal movie/TV tracking platform with smart recommendations, analytics, and user watch history. Built with Django and SQLite.

## Features

- **User Authentication**: Secure login/signup with email verification
- **TMDB Integration**: Fetch movie and TV show data from The Movie Database API
- **Watchlists**: Organize content into Plan to Watch, Watching, Completed, and Dropped lists
- **Episode Tracking**: Track progress through TV series with episode marking
- **Ratings & Reviews**: Rate and review movies/TV shows with 1-5 star ratings
- **Smart Recommendations**: Get personalized suggestions based on viewing history
- **Analytics Dashboard**: Visualize watching habits with Chart.js graphs
- **Caching**: Efficient API response caching for better performance

## Tech Stack

- **Backend**: Django 5+, Django REST Framework
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
- **APIs**: TMDB (The Movie Database)
- **Visualization**: Chart.js
- **Caching**: Django's built-in caching framework

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd CineScope-Tracker
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

1. Register a new account or login with existing credentials
2. Search for movies and TV shows using the search functionality
3. Add content to your watchlists
4. Track episode progress for TV series
5. Rate and review content
6. View recommendations on the Recommendations page
7. Check your analytics dashboard for viewing statistics

## Project Structure

```
CineScope-Tracker/
├── accounts/          # User authentication and profiles
├── analytics/         # Analytics dashboard and data visualization
├── movies/            # Movie and TV show data models and views
├── recommendations/   # Recommendation engine
├── services/          # External API services (TMDB)
├── static/            # Static files (CSS, JS, images)
├── templates/         # HTML templates
├── watchlists/        # Watchlist management
├── manage.py          # Django management script
└── cinescope/         # Main Django project settings
```

## API Keys

The application requires TMDB API keys which should be configured in environment variables:

- `TMDB_API_KEY`: Your TMDB API key
- `TMDB_READ_ACCESS_TOKEN`: Your TMDB read access token

## Deployment

The application is ready for deployment with Gunicorn and Nginx. For production deployment:

1. Set `DEBUG = False` in settings
2. Configure proper database settings
3. Set up environment variables for API keys
4. Use Gunicorn as the application server
5. Configure Nginx as a reverse proxy

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- TMDB (The Movie Database) for providing the API
- Chart.js for data visualization
- Django community for the excellent framework