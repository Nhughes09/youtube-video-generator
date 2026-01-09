"""
Metadata Generator Module
Creates optimized titles, descriptions, tags, and thumbnail prompts.
Uses AI for viral optimization.
"""

import google.generativeai as genai
from typing import List, Dict
from dataclasses import dataclass, field
import re
import json
from datetime import datetime

from config import GEMINI_API_KEY, OUTPUT_DIR
from utils import setup_logger, handle_errors
from script_generator import Script

logger = setup_logger(__name__)


@dataclass
class VideoMetadata:
    """Complete metadata for a YouTube video."""
    title_options: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    thumbnail_prompts: List[str] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)
    category: str = "Science & Technology"
    
    def get_best_title(self) -> str:
        """Return the top title option."""
        return self.title_options[0] if self.title_options else "Untitled Video"
    
    def to_dict(self) -> Dict:
        return {
            "title_options": self.title_options,
            "best_title": self.get_best_title(),
            "description": self.description,
            "tags": self.tags,
            "hashtags": self.hashtags,
            "thumbnail_prompts": self.thumbnail_prompts,
            "timestamps": self.timestamps,
            "category": self.category
        }
    
    def save(self, output_path):
        """Save metadata to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class MetadataGenerator:
    """
    Generates optimized YouTube metadata for maximum reach.
    
    Creates:
    - 10 title variations (SEO + clickbait balance)
    - Full description with timestamps
    - Relevant tags and hashtags
    - AI thumbnail prompts
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("No Gemini API key - using template-based generation")
    
    @handle_errors(retry_count=2, fallback=None)
    def generate(self, script: Script, video_duration: int = 900) -> VideoMetadata:
        """
        Generate complete metadata from script.
        
        Args:
            script: Script object with full text
            video_duration: Video length in seconds
            
        Returns:
            VideoMetadata with all fields populated
        """
        logger.info("📝 Generating video metadata...")
        
        metadata = VideoMetadata()
        
        # Generate titles
        metadata.title_options = self._generate_titles(script.topic)
        
        # Generate description with timestamps
        metadata.description = self._generate_description(script, video_duration)
        metadata.timestamps = self._extract_timestamps(video_duration)
        
        # Generate tags
        metadata.tags = self._generate_tags(script.topic)
        metadata.hashtags = self._generate_hashtags(script.topic)
        
        # Generate thumbnail prompts
        metadata.thumbnail_prompts = self._generate_thumbnail_prompts(script.topic)
        
        logger.info(f"✓ Generated metadata: {len(metadata.title_options)} titles, "
                   f"{len(metadata.tags)} tags, {len(metadata.thumbnail_prompts)} thumbnails")
        
        return metadata
    
    def _generate_titles(self, topic: str) -> List[str]:
        """Generate 10 title variations."""
        if self.model:
            prompt = f"""Generate 10 viral YouTube video titles for this topic:

Topic: {topic}

Requirements:
- Mix of emotional hooks (fear, curiosity, urgency)
- Include numbers/years where relevant (e.g., "2026")
- Some should be mild clickbait, some straightforward
- 50-70 characters each (YouTube optimal)
- Use power words: Breaking, Shocking, Warning, Finally, etc.

Examples of good patterns:
- "The AI Revolution Is Here: How X Is Changing Everything in 2026"
- "WARNING: X Could Replace Your Job by 2026 (Here's What to Do)"
- "I Spent 30 Days Researching AI Job Loss - This Is What I Found"

Return ONLY the 10 titles, numbered 1-10:"""
            
            try:
                response = self.model.generate_content(prompt)
                titles = []
                for line in response.text.strip().split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit():
                        # Remove number prefix
                        title = re.sub(r'^\d+[\.\)]\s*', '', line)
                        if title:
                            titles.append(title)
                return titles[:10]
            except Exception as e:
                logger.warning(f"AI title generation failed: {e}")
        
        # Fallback templates
        return [
            f"🤖 {topic} - What You Need to Know in 2026",
            f"WARNING: {topic} Is Changing Everything",
            f"The Truth About {topic} (Nobody's Talking About This)",
            f"How {topic} Will Affect Your Career in 2026",
            f"{topic} Explained: The Complete 2026 Breakdown",
            f"🚨 BREAKING: {topic} - Full Analysis",
            f"Why {topic} Should Worry Everyone",
            f"I Researched {topic} - Here's What I Found",
            f"{topic}: Opportunities vs Threats [Expert Analysis]",
            f"The Future of Work: {topic} in 2026",
        ]
    
    def _generate_description(self, script: Script, duration: int) -> str:
        """Generate SEO-optimized description."""
        # Extract key points from script for description
        hook = script.hook[:200] if script.hook else ""
        
        timestamps = self._extract_timestamps(duration)
        timestamp_text = "\n".join(timestamps)
        
        description = f"""📺 {script.topic}

{hook}

In this comprehensive breakdown, we explore the latest developments in AI and robotics, analyzing the real implications for jobs and the economy in 2026 and beyond.

⏱️ TIMESTAMPS:
{timestamp_text}

🔔 SUBSCRIBE for more AI & technology analysis!
👍 LIKE if you found this informative
💬 COMMENT your thoughts - Do you think AI will help or hurt workers?

#AI #Robotics #Technology #FutureOfWork #Automation #ArtificialIntelligence #Jobs2026

📚 SOURCES & RESEARCH:
This video compiles analysis from various news sources and studies. All visuals are stock footage or AI-generated for educational purposes.

⚠️ DISCLAIMER:
This content is for educational and informational purposes only. Always do your own research before making career or financial decisions.

© 2026 [Channel Name] - All Rights Reserved
"""
        return description.strip()
    
    def _extract_timestamps(self, duration: int) -> List[str]:
        """Create timestamps matching video structure."""
        return [
            "0:00 - Introduction & Hook",
            "0:30 - Overview: What We'll Cover",
            "2:00 - The Current State of AI & Robotics",
            "4:00 - Key Development #1",
            "6:00 - Key Development #2", 
            "8:00 - Key Development #3",
            "10:00 - Job Displacement Analysis",
            "12:00 - Implications: Fears vs Opportunities",
            "14:00 - Expert Predictions",
            f"{duration // 60}:00 - Conclusion & What You Can Do",
        ]
    
    def _generate_tags(self, topic: str) -> List[str]:
        """Generate relevant tags for SEO."""
        base_tags = [
            "AI", "artificial intelligence", "robots", "robotics",
            "automation", "future of work", "job loss", "unemployment",
            "technology 2026", "AI news", "robot workers", "ChatGPT",
            "machine learning", "tech news", "job displacement",
            "AI revolution", "workforce automation", "career advice",
            "AI jobs", "technology trends"
        ]
        
        # Add topic-specific words
        topic_words = topic.lower().replace(",", "").split()
        for word in topic_words:
            if len(word) > 3 and word not in ["the", "and", "for", "that", "this"]:
                base_tags.append(word)
        
        return list(set(base_tags))[:30]  # YouTube limit
    
    def _generate_hashtags(self, topic: str) -> List[str]:
        """Generate trending hashtags."""
        return [
            "#AI2026", "#Robotics", "#FutureOfWork", "#Automation",
            "#TechNews", "#ArtificialIntelligence", "#JobsOfTheFuture",
            "#MachineLearning", "#Innovation", "#TechTrends"
        ]
    
    def _generate_thumbnail_prompts(self, topic: str) -> List[str]:
        """Generate AI image prompts for thumbnails."""
        return [
            f"Dramatic thumbnail: humanoid robot in office replacing human worker, "
            f"red warning colors, bold text space, photorealistic, 4K, cinematic lighting",
            
            f"Shocked person looking at futuristic AI robot, split image, "
            f"before/after style, dramatic lighting, YouTube thumbnail style",
            
            f"Robot hand and human hand reaching toward each other, "
            f"dramatic blue and orange lighting, movie poster style, 4K",
            
            f"Futuristic cityscape with robots, worried crowd of workers, "
            f"dramatic sky, news broadcast style, bold colors",
            
            f"AI brain visualization with job icons being absorbed, "
            f"dark dramatic background, glowing elements, tech aesthetic"
        ]


# =============================================================================
# CLI USAGE
# =============================================================================

if __name__ == "__main__":
    from script_generator import Script
    
    # Create test script
    test_script = Script(
        topic="AI Mass Layoffs in 2026: The Complete Breakdown",
        full_text="Test script content...",
        hook="What if I told you that robots will replace 50 million jobs by 2026?",
        word_count=2000
    )
    
    generator = MetadataGenerator()
    metadata = generator.generate(test_script)
    
    print("\n📋 GENERATED METADATA\n" + "="*50)
    print(f"\n🎯 TITLE OPTIONS:")
    for i, title in enumerate(metadata.title_options, 1):
        print(f"  {i}. {title}")
    
    print(f"\n🏷️ TAGS ({len(metadata.tags)}):")
    print(f"  {', '.join(metadata.tags[:10])}...")
    
    print(f"\n🖼️ THUMBNAIL PROMPTS:")
    print(f"  {metadata.thumbnail_prompts[0][:100]}...")
