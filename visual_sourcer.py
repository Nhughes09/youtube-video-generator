"""
Visual Sourcer Module
Fetches stock footage, images from Pexels/Pixabay, and generates AI images via Pollinations.
100% free and copyright-safe sources only.
"""

import requests
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import time
import urllib.parse
import os

from config import (
    PEXELS_API_KEY, PIXABAY_API_KEY, 
    API_ENDPOINTS, CONTENT_CONFIG, TEMP_DIR
)
from utils import setup_logger, handle_errors, sanitize_filename

logger = setup_logger(__name__)


@dataclass
class Visual:
    """Represents a visual asset (image or video)."""
    id: str
    type: str  # "video" or "image"
    source: str  # "pexels", "pixabay", "pollinations"
    url: str
    download_url: str
    local_path: Optional[str] = None
    width: int = 0
    height: int = 0
    duration: float = 0  # For videos
    description: str = ""


class VisualSourcer:
    """
    Sources visuals from free stock sites and AI generators.
    
    Sources (all FREE):
    - Pexels: Stock videos/photos, 200 requests/hour
    - Pixabay: Stock videos/photos, 100 requests/minute  
    - Pollinations.ai: AI image generation, UNLIMITED, no key!
    """
    
    def __init__(self):
        self.pexels_key = PEXELS_API_KEY
        self.pixabay_key = PIXABAY_API_KEY
        self.session = requests.Session()
        self.download_dir = TEMP_DIR / "visuals"
        self.download_dir.mkdir(exist_ok=True)
        
        # Track API usage
        self.api_calls = {"pexels": 0, "pixabay": 0}
    
    # =========================================================================
    # PEXELS API
    # =========================================================================
    
    @handle_errors(retry_count=2, retry_delay=1.0, fallback=[])
    def search_pexels_videos(self, query: str, count: int = 5) -> List[Visual]:
        """Search Pexels for stock videos."""
        if not self.pexels_key:
            logger.warning("No Pexels API key - skipping Pexels videos")
            return []
        
        visuals = []
        url = API_ENDPOINTS["pexels_videos"]
        
        response = self.session.get(
            url,
            headers={"Authorization": self.pexels_key},
            params={"query": query, "per_page": count, "orientation": "landscape"},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        self.api_calls["pexels"] += 1
        
        for video in data.get("videos", []):
            # Get HD or SD file
            video_files = video.get("video_files", [])
            hd_file = next(
                (f for f in video_files if f.get("quality") == "hd"),
                video_files[0] if video_files else None
            )
            
            if hd_file:
                visuals.append(Visual(
                    id=f"pexels_{video['id']}",
                    type="video",
                    source="pexels",
                    url=video.get("url", ""),
                    download_url=hd_file.get("link", ""),
                    width=hd_file.get("width", 1920),
                    height=hd_file.get("height", 1080),
                    duration=video.get("duration", 10),
                    description=query
                ))
        
        logger.info(f"Pexels videos '{query}': found {len(visuals)}")
        return visuals
    
    @handle_errors(retry_count=2, retry_delay=1.0, fallback=[])
    def search_pexels_photos(self, query: str, count: int = 5) -> List[Visual]:
        """Search Pexels for stock photos."""
        if not self.pexels_key:
            return []
        
        visuals = []
        url = API_ENDPOINTS["pexels_photos"]
        
        response = self.session.get(
            url,
            headers={"Authorization": self.pexels_key},
            params={"query": query, "per_page": count, "orientation": "landscape"},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        self.api_calls["pexels"] += 1
        
        for photo in data.get("photos", []):
            visuals.append(Visual(
                id=f"pexels_{photo['id']}",
                type="image",
                source="pexels",
                url=photo.get("url", ""),
                download_url=photo.get("src", {}).get("large2x", ""),
                width=photo.get("width", 1920),
                height=photo.get("height", 1080),
                description=query
            ))
        
        logger.info(f"Pexels photos '{query}': found {len(visuals)}")
        return visuals
    
    # =========================================================================
    # PIXABAY API
    # =========================================================================
    
    @handle_errors(retry_count=2, retry_delay=1.0, fallback=[])
    def search_pixabay_videos(self, query: str, count: int = 5) -> List[Visual]:
        """Search Pixabay for stock videos."""
        if not self.pixabay_key:
            logger.warning("No Pixabay API key - skipping Pixabay videos")
            return []
        
        visuals = []
        url = API_ENDPOINTS["pixabay_videos"]
        
        response = self.session.get(
            url,
            params={
                "key": self.pixabay_key,
                "q": query,
                "per_page": count,
                "video_type": "all"
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        self.api_calls["pixabay"] += 1
        
        for video in data.get("hits", []):
            videos = video.get("videos", {})
            # Prefer large, then medium
            video_data = videos.get("large") or videos.get("medium") or {}
            
            if video_data:
                visuals.append(Visual(
                    id=f"pixabay_{video['id']}",
                    type="video",
                    source="pixabay",
                    url=video.get("pageURL", ""),
                    download_url=video_data.get("url", ""),
                    width=video_data.get("width", 1920),
                    height=video_data.get("height", 1080),
                    duration=video.get("duration", 10),
                    description=query
                ))
        
        logger.info(f"Pixabay videos '{query}': found {len(visuals)}")
        return visuals
    
    @handle_errors(retry_count=2, retry_delay=1.0, fallback=[])
    def search_pixabay_images(self, query: str, count: int = 5) -> List[Visual]:
        """Search Pixabay for stock images."""
        if not self.pixabay_key:
            return []
        
        visuals = []
        url = API_ENDPOINTS["pixabay"]
        
        response = self.session.get(
            url,
            params={
                "key": self.pixabay_key,
                "q": query,
                "per_page": count,
                "image_type": "all",
                "orientation": "horizontal"
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        self.api_calls["pixabay"] += 1
        
        for image in data.get("hits", []):
            visuals.append(Visual(
                id=f"pixabay_{image['id']}",
                type="image",
                source="pixabay",
                url=image.get("pageURL", ""),
                download_url=image.get("largeImageURL", ""),
                width=image.get("imageWidth", 1920),
                height=image.get("imageHeight", 1080),
                description=query
            ))
        
        logger.info(f"Pixabay images '{query}': found {len(visuals)}")
        return visuals
    
    # =========================================================================
    # POLLINATIONS.AI (FREE AI IMAGE GENERATION)
    # =========================================================================
    
    def generate_ai_image(self, prompt: str, width: int = 1920, height: int = 1080) -> Visual:
        """
        Generate AI image via Pollinations.ai.
        100% FREE, no API key required, unlimited!
        """
        # Clean and encode prompt
        clean_prompt = prompt.replace('\n', ' ').strip()
        encoded_prompt = urllib.parse.quote(clean_prompt)
        
        # Build URL (image is generated on request)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}"
        
        visual = Visual(
            id=f"pollinations_{hash(prompt) % 10000000}",
            type="image",
            source="pollinations",
            url=url,
            download_url=url,
            width=width,
            height=height,
            description=prompt
        )
        
        logger.info(f"Generated AI image prompt: {prompt[:50]}...")
        return visual
    
    def generate_ai_images_from_script(self, script_text: str, count: int = 5) -> List[Visual]:
        """
        Extract visual cues from script and generate AI images.
        Looks for [VISUAL: description] markers.
        """
        import re
        
        visuals = []
        
        # Find visual markers
        visual_cues = re.findall(r'\[VISUAL:\s*([^\]]+)\]', script_text, re.IGNORECASE)
        
        for cue in visual_cues[:count]:
            # Enhance prompt for better AI generation
            enhanced_prompt = f"photorealistic, 4k, cinematic lighting, {cue}, technology, futuristic"
            visual = self.generate_ai_image(enhanced_prompt)
            visuals.append(visual)
        
        # If not enough cues, generate generic tech visuals
        if len(visuals) < count:
            generic_prompts = [
                "futuristic humanoid robot in modern office, photorealistic, 4k",
                "artificial intelligence neural network visualization, blue glow, cinematic",
                "worried office workers looking at computer screens, corporate setting",
                "automation factory with robots, dramatic lighting",
                "person shaking hands with android robot, photorealistic",
            ]
            for prompt in generic_prompts[:count - len(visuals)]:
                visuals.append(self.generate_ai_image(prompt))
        
        logger.info(f"Generated {len(visuals)} AI images")
        return visuals
    
    # =========================================================================
    # DOWNLOAD & COLLECTION
    # =========================================================================
    
    @handle_errors(retry_count=3, retry_delay=2.0)
    def download_visual(self, visual: Visual) -> Visual:
        """Download a visual to local storage."""
        ext = "mp4" if visual.type == "video" else "jpg"
        filename = f"{visual.id}.{ext}"
        filepath = self.download_dir / filename
        
        if filepath.exists():
            visual.local_path = str(filepath)
            return visual
        
        logger.info(f"Downloading: {visual.id}")
        
        response = self.session.get(visual.download_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        visual.local_path = str(filepath)
        logger.info(f"Downloaded: {filepath.name}")
        return visual
    
    def collect_visuals_for_topic(
        self,
        topic: str,
        script_text: str = "",
        target_count: int = 15
    ) -> List[Visual]:
        """
        Collect all visuals needed for a video.
        Mix of stock footage/images and AI-generated images.
        """
        logger.info(f"🎬 Collecting visuals for: {topic[:50]}...")
        
        all_visuals = []
        keywords = CONTENT_CONFIG["visual_keywords"][:5]  # Top 5 keywords
        
        # 1. Search stock videos (primary B-roll)
        for keyword in keywords[:3]:
            all_visuals.extend(self.search_pexels_videos(keyword, count=2))
            all_visuals.extend(self.search_pixabay_videos(keyword, count=2))
            time.sleep(0.5)  # Rate limiting
        
        # 2. Search stock images
        for keyword in keywords:
            all_visuals.extend(self.search_pexels_photos(keyword, count=2))
            all_visuals.extend(self.search_pixabay_images(keyword, count=2))
            time.sleep(0.5)
        
        # 3. Generate AI images from script cues
        ai_images = self.generate_ai_images_from_script(
            script_text, 
            count=max(5, target_count - len(all_visuals))
        )
        all_visuals.extend(ai_images)
        
        # Deduplicate
        seen_ids = set()
        unique_visuals = []
        for v in all_visuals:
            if v.id not in seen_ids:
                seen_ids.add(v.id)
                unique_visuals.append(v)
        
        # Limit to target
        final_visuals = unique_visuals[:target_count]
        
        logger.info(f"✓ Collected {len(final_visuals)} visuals "
                   f"({sum(1 for v in final_visuals if v.type == 'video')} videos, "
                   f"{sum(1 for v in final_visuals if v.type == 'image')} images)")
        
        return final_visuals
    
    def download_all(self, visuals: List[Visual]) -> List[Visual]:
        """Download all visuals to local storage."""
        logger.info(f"⬇️ Downloading {len(visuals)} visuals...")
        
        downloaded = []
        for visual in visuals:
            try:
                downloaded_visual = self.download_visual(visual)
                downloaded.append(downloaded_visual)
            except Exception as e:
                logger.warning(f"Failed to download {visual.id}: {e}")
        
        logger.info(f"✓ Downloaded {len(downloaded)}/{len(visuals)} visuals")
        return downloaded


# =============================================================================
# CLI USAGE
# =============================================================================

if __name__ == "__main__":
    sourcer = VisualSourcer()
    
    # Test AI image generation (no API key needed!)
    print("\n🎨 Testing Pollinations.ai (FREE, no key):")
    ai_image = sourcer.generate_ai_image("futuristic robot replacing human worker, cinematic")
    print(f"AI Image URL: {ai_image.url[:80]}...")
    
    # Test stock search (needs API keys)
    print("\n📷 Testing stock photo search:")
    visuals = sourcer.search_pexels_photos("artificial intelligence", count=3)
    for v in visuals:
        print(f"  - {v.source}: {v.description}")
    
    print("\n✓ Visual sourcer working!")
