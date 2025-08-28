# Cathode Backend Setup

## Required Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# Spotify API Credentials
# Get these from https://developer.spotify.com/dashboard/applications
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# Google Generative AI API Key (either name works)
# Get this from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_google_api_key_here
# OR
# GOOGLE_API_KEY=your_google_api_key_here
```

## Setup Steps

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Spotify API Credentials:**
   - Go to https://developer.spotify.com/dashboard/applications
   - Create a new application
   - Copy the Client ID and Client Secret

3. **Get Google AI API Key:**
   - Go to https://makersuite.google.com/app/apikey
   - Create a new API key
   - Copy the API key

4. **Create .env file:**
   ```bash
   touch .env
   # Then add the credentials above
   ```

5. **Start the server:**
   ```bash
   python start_server.py
   ```

The API will be available at http://localhost:8000
