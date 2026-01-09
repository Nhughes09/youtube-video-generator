"""
AI Video Generator - Configuration
All API keys and settings for the video generation pipeline.

FREE SIGNUP LINKS:
- Pexels: https://www.pexels.com/api/
- Pixabay: https://pixabay.com/api/docs/
- Google Gemini: https://aistudio.google.com/api-keys
- Google Cloud TTS: https://cloud.google.com/text-to-speech (free tier)
- HuggingFace: https://huggingface.co/settings/tokens
- Pollinations.ai: https://pollinations.ai/ (NO KEY NEEDED!)
"""

import os
from pathlib import Path

# =============================================================================
# API KEYS (Get free keys from links above)
# =============================================================================

# Google Gemini (free tier: 60 requests/minute)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Pexels (free: 200 requests/hour)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Pixabay (free: 100 requests/minute)
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

# HuggingFace (free tier: 30k tokens/month)
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# Google Cloud TTS (optional - uses gTTS as free fallback)
GOOGLE_CLOUD_TTS_KEY = os.getenv("GOOGLE_CLOUD_TTS_KEY", "")

# =============================================================================
# DIRECTORIES
# =============================================================================

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Create directories
for dir_path in [OUTPUT_DIR, ASSETS_DIR, TEMP_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# =============================================================================
# VIDEO SETTINGS
# =============================================================================

VIDEO_CONFIG = {
    # Target duration (seconds)
    "target_duration": 900,  # 15 minutes
    "min_duration": 840,     # 14 minutes
    "max_duration": 1200,    # 20 minutes
    
    # Resolution
    "width": 1920,
    "height": 1080,
    "fps": 30,
    
    # Shorts settings
    "shorts_duration": 59,   # Under 60 seconds
    "shorts_width": 1080,
    "shorts_height": 1920,
    
    # Audio
    "voice_speed": 1.0,
    "background_music_volume": 0.1,
}

# =============================================================================
# SCRIPT SETTINGS
# =============================================================================

SCRIPT_CONFIG = {
    # Word counts (approx 150 words/minute for speech)
    "target_words": 2250,     # ~15 min
    "min_words": 2000,        # ~13 min
    "max_words": 2700,        # ~18 min
    
    # Structure (percentage of total)
    "hook_percent": 3,        # 0:00-0:30
    "overview_percent": 10,   # 0:30-2:00
    "breakdown_percent": 60,  # 2:00-12:00
    "implications_percent": 17, # 12:00-15:00
    "conclusion_percent": 10, # 15:00+
    
    # Key points in breakdown
    "num_key_points": 6,
}

# =============================================================================
# CONTENT SETTINGS
# =============================================================================

CONTENT_CONFIG = {
    # Topics to track
    "keywords": [
        "AI layoffs 2026",
        "robotics unemployment", 
        "artificial intelligence jobs",
        "automation job loss",
        "humanoid robots workers",
        "ChatGPT replacing jobs",
        "AI mass unemployment",
        "robot workforce 2026",
    ],
    
    # News sources (RSS feeds)
    "rss_feeds": [
        "https://news.google.com/rss/search?q=AI+robots+jobs+2026&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=artificial+intelligence+unemployment&hl=en-US&gl=US&ceid=US:en",
    ],
    
    # Reddit sources
    "reddit_subs": [
        "Futurology",
        "singularity", 
        "artificial",
        "technology",
    ],
    
    # Visual search terms
    "visual_keywords": [
        "humanoid robot",
        "artificial intelligence",
        "office automation",
        "futuristic technology",
        "robot worker",
        "digital brain",
        "job interview",
        "unemployment line",
    ],
}

# =============================================================================
# API ENDPOINTS
# =============================================================================

API_ENDPOINTS = {
    "pexels_videos": "https://api.pexels.com/videos/search",
    "pexels_photos": "https://api.pexels.com/v1/search",
    "pixabay": "https://pixabay.com/api/",
    "pixabay_videos": "https://pixabay.com/api/videos/",
    "pollinations": "https://image.pollinations.ai/prompt/{}",
    "reddit": "https://www.reddit.com/r/{}/new.json",
}

# =============================================================================
# LOGGING
# =============================================================================

LOG_CONFIG = {
    "level": "INFO",
    "file": LOGS_DIR / "video_generator.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}
