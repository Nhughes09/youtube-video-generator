"""
YouTube Integration Module
Upload videos and fetch analytics for learning and optimization.

Channel: @airobotsunemployment
Focus: AI / Robots / Unemployment

This module provides:
- Video upload automation
- Analytics fetching for learning
- Performance pattern recognition
- Content optimization recommendations
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from config import LOGS_DIR, OUTPUT_DIR
from utils import setup_logger, handle_errors
from reasoning_engine import reasoning, think, decide

logger = setup_logger(__name__)


# =============================================================================
# CHANNEL CONFIGURATION
# =============================================================================

CHANNEL_CONFIG = {
    "name": "Ai / Robots / Unemployment",
    "handle": "@airobotsunemployment",
    "focus_topics": [
        "artificial intelligence",
        "robotics",
        "automation",
        "job displacement",
        "unemployment",
        "future of work",
    ],
    "target_video_length": 900,  # 15 minutes
    "optimal_upload_times": ["09:00", "14:00", "18:00"],  # EST
    "hashtags": [
        "#AI2026", "#Robotics", "#Unemployment", "#FutureOfWork",
        "#Automation", "#ArtificialIntelligence", "#TechNews"
    ],
    "branding": {
        "intro_text": "Welcome to AI Robots Unemployment",
        "outro_text": "Subscribe for more AI and robotics news!",
        "watermark": None,  # Path to watermark image
    }
}


# =============================================================================
# YOUTUBE DATA API CLIENT
# =============================================================================

@dataclass
class YouTubeVideo:
    """Represents a YouTube video (uploaded or to upload)."""
    video_id: str = ""
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    category_id: str = "28"  # Science & Technology
    privacy_status: str = "private"  # Start private, review before public
    local_path: Optional[Path] = None
    thumbnail_path: Optional[Path] = None
    upload_time: Optional[str] = None
    
    # Analytics (populated after upload)
    views: int = 0
    likes: int = 0
    comments: int = 0
    watch_time_hours: float = 0
    retention_percent: float = 0
    ctr_percent: float = 0


class YouTubeClient:
    """
    YouTube Data API client for upload and analytics.
    
    SETUP REQUIRED:
    1. Go to https://console.cloud.google.com/
    2. Create a new project
    3. Enable YouTube Data API v3
    4. Create OAuth 2.0 credentials
    5. Download client_secrets.json to project root
    
    First run will open browser for OAuth authentication.
    """
    
    def __init__(self, credentials_file: str = "client_secrets.json"):
        self.credentials_file = Path(credentials_file)
        self.token_file = LOGS_DIR / "youtube_token.json"
        self.channel_config = CHANNEL_CONFIG
        self.youtube = None
        
        # Track upload history for learning
        self.upload_history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Load upload history for pattern learning."""
        history_file = LOGS_DIR / "youtube_history.json"
        if history_file.exists():
            with open(history_file) as f:
                return json.load(f)
        return []
    
    def _save_history(self):
        """Save upload history."""
        history_file = LOGS_DIR / "youtube_history.json"
        with open(history_file, 'w') as f:
            json.dump(self.upload_history, f, indent=2)
    
    @handle_errors(retry_count=2, fallback=False)
    def authenticate(self) -> bool:
        """Authenticate with YouTube API using OAuth."""
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            SCOPES = [
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/yt-analytics.readonly'
            ]
            
            creds = None
            
            # Load existing token
            if self.token_file.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_file.exists():
                        logger.warning(f"⚠️ Missing {self.credentials_file}")
                        logger.warning("Download from Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), SCOPES
                    )
                    creds = flow.run_local_server(port=8080)
                
                # Save token for next run
                with open(self.token_file, 'w') as f:
                    f.write(creds.to_json())
            
            self.youtube = build('youtube', 'v3', credentials=creds)
            think("observation", "YouTube API authenticated successfully")
            logger.info("✓ YouTube API authenticated")
            return True
            
        except ImportError:
            logger.warning("⚠️ Google API libraries not installed")
            logger.warning("Run: pip install google-auth-oauthlib google-api-python-client")
            return False
        except Exception as e:
            logger.error(f"YouTube auth failed: {e}")
            return False
    
    @handle_errors(retry_count=2, fallback=None)
    def upload_video(self, video: YouTubeVideo) -> Optional[str]:
        """
        Upload a video to YouTube.
        
        Returns video ID if successful.
        """
        if not self.youtube:
            if not self.authenticate():
                return None
        
        from googleapiclient.http import MediaFileUpload
        
        think("analysis", f"Uploading video: {video.title[:40]}...")
        logger.info(f"📤 Uploading to YouTube: {video.title[:50]}...")
        
        body = {
            'snippet': {
                'title': video.title,
                'description': video.description,
                'tags': video.tags,
                'categoryId': video.category_id
            },
            'status': {
                'privacyStatus': video.privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(
            str(video.local_path),
            chunksize=1024*1024,
            resumable=True
        )
        
        request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                logger.info(f"   Upload progress: {progress}%")
        
        video_id = response['id']
        video.video_id = video_id
        video.upload_time = datetime.now().isoformat()
        
        # Set thumbnail if provided
        if video.thumbnail_path and video.thumbnail_path.exists():
            self._set_thumbnail(video_id, video.thumbnail_path)
        
        # Record in history
        self.upload_history.append({
            "video_id": video_id,
            "title": video.title,
            "upload_time": video.upload_time,
            "privacy": video.privacy_status,
            "local_path": str(video.local_path)
        })
        self._save_history()
        
        think("insight", f"Video uploaded: {video_id}")
        logger.info(f"✅ Uploaded: https://youtube.com/watch?v={video_id}")
        
        return video_id
    
    def _set_thumbnail(self, video_id: str, thumbnail_path: Path):
        """Set video thumbnail."""
        from googleapiclient.http import MediaFileUpload
        
        try:
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path))
            ).execute()
            logger.info("   ✓ Thumbnail set")
        except Exception as e:
            logger.warning(f"   ⚠️ Thumbnail failed: {e}")
    
    # =========================================================================
    # ANALYTICS FOR LEARNING
    # =========================================================================
    
    @handle_errors(retry_count=2, fallback={})
    def get_video_analytics(self, video_id: str) -> Dict:
        """Fetch analytics for a video."""
        if not self.youtube:
            if not self.authenticate():
                return {}
        
        # Get video statistics
        response = self.youtube.videos().list(
            part='statistics,contentDetails',
            id=video_id
        ).execute()
        
        if not response.get('items'):
            return {}
        
        stats = response['items'][0]['statistics']
        
        analytics = {
            "video_id": video_id,
            "views": int(stats.get('viewCount', 0)),
            "likes": int(stats.get('likeCount', 0)),
            "comments": int(stats.get('commentCount', 0)),
            "fetched_at": datetime.now().isoformat()
        }
        
        return analytics
    
    @handle_errors(retry_count=2, fallback=[])
    def get_channel_videos(self, max_results: int = 20) -> List[Dict]:
        """Get recent videos from the channel."""
        if not self.youtube:
            if not self.authenticate():
                return []
        
        # Get channel uploads playlist
        channels = self.youtube.channels().list(
            part='contentDetails',
            mine=True
        ).execute()
        
        if not channels.get('items'):
            return []
        
        uploads_playlist = channels['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from playlist
        videos = self.youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist,
            maxResults=max_results
        ).execute()
        
        return [
            {
                "video_id": item['snippet']['resourceId']['videoId'],
                "title": item['snippet']['title'],
                "published_at": item['snippet']['publishedAt']
            }
            for item in videos.get('items', [])
        ]
    
    def analyze_performance_patterns(self) -> Dict:
        """
        Analyze channel performance to learn optimal patterns.
        Used by reasoning engine for content optimization.
        """
        think("analysis", "Analyzing channel performance patterns...")
        
        patterns = {
            "best_performing_titles": [],
            "optimal_length": None,
            "best_upload_time": None,
            "top_tags": [],
            "avg_views": 0,
            "avg_retention": 0
        }
        
        videos = self.get_channel_videos(max_results=50)
        
        if not videos:
            return patterns
        
        # Collect analytics for each video
        video_data = []
        for video in videos[:20]:  # Limit API calls
            analytics = self.get_video_analytics(video['video_id'])
            if analytics:
                video_data.append({**video, **analytics})
        
        if video_data:
            # Calculate averages
            total_views = sum(v.get('views', 0) for v in video_data)
            patterns['avg_views'] = total_views // len(video_data)
            
            # Find best performers
            sorted_by_views = sorted(video_data, key=lambda x: x.get('views', 0), reverse=True)
            patterns['best_performing_titles'] = [v['title'] for v in sorted_by_views[:5]]
            
            think("insight", f"Channel avg views: {patterns['avg_views']}")
            think("insight", f"Top video: {patterns['best_performing_titles'][0] if patterns['best_performing_titles'] else 'N/A'}")
        
        # Save patterns for reasoning engine
        patterns_file = LOGS_DIR / "youtube_patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)
        
        logger.info(f"📊 Channel patterns saved to {patterns_file.name}")
        return patterns


# =============================================================================
# UPLOAD MANAGER (HIGH-LEVEL)
# =============================================================================

class YouTubeUploadManager:
    """
    High-level manager for YouTube uploads.
    Integrates with the video pipeline output.
    """
    
    def __init__(self):
        self.client = YouTubeClient()
        self.channel = CHANNEL_CONFIG
    
    def prepare_upload(
        self,
        video_path: Path,
        metadata_path: Path,
        thumbnail_path: Path = None,
        privacy: str = "private"
    ) -> YouTubeVideo:
        """Prepare a video for upload from pipeline output."""
        
        # Load metadata
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        video = YouTubeVideo(
            title=metadata.get('best_title', metadata.get('title_options', ['Untitled'])[0]),
            description=metadata.get('description', ''),
            tags=metadata.get('tags', []),
            privacy_status=privacy,
            local_path=video_path,
            thumbnail_path=thumbnail_path
        )
        
        return video
    
    def upload_from_output(
        self,
        project_id: str,
        make_public: bool = False
    ) -> Optional[str]:
        """
        Upload a video from pipeline output directory.
        
        Args:
            project_id: The video project ID (from main.py)
            make_public: If True, upload as public immediately
            
        Returns:
            YouTube video ID if successful
        """
        # Find video file
        video_files = list(OUTPUT_DIR.glob(f"{project_id}*.mp4"))
        if not video_files:
            logger.error(f"No video found for project: {project_id}")
            return None
        
        video_path = video_files[0]
        
        # Find metadata
        metadata_files = list(OUTPUT_DIR.glob(f"{project_id}*_metadata.json"))
        if not metadata_files:
            logger.error(f"No metadata found for project: {project_id}")
            return None
        
        metadata_path = metadata_files[0]
        
        # Prepare and upload
        video = self.prepare_upload(
            video_path=video_path,
            metadata_path=metadata_path,
            privacy="public" if make_public else "private"
        )
        
        think("decision", f"Uploading as {'public' if make_public else 'private'}")
        
        return self.client.upload_video(video)
    
    def learn_from_channel(self):
        """Fetch and analyze channel data for learning."""
        return self.client.analyze_performance_patterns()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube Integration")
    parser.add_argument("--auth", action="store_true", help="Test authentication")
    parser.add_argument("--analyze", action="store_true", help="Analyze channel patterns")
    parser.add_argument("--upload", type=str, help="Upload video by project ID")
    
    args = parser.parse_args()
    
    manager = YouTubeUploadManager()
    
    if args.auth:
        print("🔑 Testing YouTube API authentication...")
        if manager.client.authenticate():
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed. Check credentials.")
    
    elif args.analyze:
        print("📊 Analyzing channel performance...")
        patterns = manager.learn_from_channel()
        print(f"Average views: {patterns.get('avg_views', 'N/A')}")
        print(f"Top videos: {patterns.get('best_performing_titles', [])[:3]}")
    
    elif args.upload:
        print(f"📤 Uploading project: {args.upload}")
        video_id = manager.upload_from_output(args.upload)
        if video_id:
            print(f"✅ Uploaded: https://youtube.com/watch?v={video_id}")
    
    else:
        print("YouTube Integration for @airobotsunemployment")
        print("Use --help for options")
