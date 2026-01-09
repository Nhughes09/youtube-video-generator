"""
Script Generator Module
Uses Google Gemini API to create engaging 15-20 minute video scripts.
"""

import google.generativeai as genai
from typing import Dict, Optional
from dataclasses import dataclass, field
import re

from config import GEMINI_API_KEY, SCRIPT_CONFIG
from utils import setup_logger, handle_errors, estimate_duration
from topic_discovery import Topic

logger = setup_logger(__name__)


@dataclass
class Script:
    """Represents a generated video script."""
    topic: str
    full_text: str
    hook: str = ""
    overview: str = ""
    breakdown: str = ""
    implications: str = ""
    conclusion: str = ""
    word_count: int = 0
    estimated_duration: int = 0
    shorts_excerpts: list = field(default_factory=list)
    
    def __post_init__(self):
        self.word_count = len(self.full_text.split())
        self.estimated_duration = estimate_duration(self.word_count)


class ScriptGenerator:
    """
    Generates video scripts using Google Gemini API.
    Free tier: 60 requests/minute, 1M tokens/day.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY required. Get free at: https://aistudio.google.com/api-keys")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Free tier model
        
        self.script_template = self._build_template()
    
    def _build_template(self) -> str:
        """Build the script generation prompt template."""
        return """You are an expert YouTube script writer specializing in AI and technology content.
Create a compelling, well-researched script for a 15-20 minute video.

TOPIC: {topic}

ADDITIONAL CONTEXT:
{context}

SCRIPT STRUCTURE (follow this exactly):

## HOOK (0:00-0:30) - ~75 words
Start with a shocking statistic or provocative question that stops scrollers.
Create immediate emotional impact about AI/job displacement.
Example opening: "What if I told you that by the end of 2026, the robot you're about to see will have replaced over 1 million jobs?"

## OVERVIEW (0:30-2:00) - ~200 words
Summarize what this video covers and why viewers MUST watch until the end.
Establish credibility and promise valuable insights.
Tease the most shocking revelation coming later.

## DEEP BREAKDOWN (2:00-12:00) - ~1500 words
Cover 5-7 key points with:
- Specific facts, statistics, and timelines
- Real company names and announcements
- Original analysis on unemployment implications
- Cause-and-effect explanations
- Visual cue suggestions in [VISUAL: description] format

Structure each point as:
**Point X: [Compelling Title]**
[Detailed explanation with facts]
[VISUAL: suggestion for b-roll or graphic]
[Analysis of job displacement impact]

## IMPLICATIONS & BALANCE (12:00-15:00) - ~400 words
Present both sides fairly:
- The fears and genuine concerns about mass unemployment
- The opportunities and potential positive outcomes
- Expert quotes or predictions (attribute properly)
- What workers can do to adapt

## CONCLUSION & CTA (15:00+) - ~150 words
- Summarize the 3 most important takeaways
- Make a bold but reasonable prediction
- Ask viewers an engaging question to comment on
- Strong subscribe call-to-action
- Tease next video topic

## SHORTS EXCERPTS
Provide 3-5 standalone 30-second excerpts that could go viral as YouTube Shorts.
Each should be self-contained with a hook and payoff.

---

WRITING STYLE GUIDELINES:
- Conversational but authoritative
- Use "you" and "we" to engage viewers
- Include natural pauses marked with "..." or "[PAUSE]"
- Avoid clickbait feel - deliver on promises
- Be factual but create emotional impact
- Support fair use by providing heavy original analysis and commentary

NOW WRITE THE COMPLETE SCRIPT:"""
    
    @handle_errors(retry_count=3, retry_delay=5.0)
    def generate(self, topic: Topic, additional_context: str = "") -> Script:
        """
        Generate a complete video script from a topic.
        
        Args:
            topic: Topic object from discovery
            additional_context: Optional extra info to include
            
        Returns:
            Script object with full text and sections
        """
        logger.info(f"📝 Generating script for: {topic.title[:50]}...")
        
        # Build prompt
        context = f"""
Title: {topic.title}
Source: {topic.source}
Summary: {topic.summary}
Keywords: {', '.join(topic.keywords_matched)}
{additional_context}
""".strip()
        
        prompt = self.script_template.format(
            topic=topic.title,
            context=context
        )
        
        # Generate with Gemini
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4000,
            )
        )
        
        full_text = response.text
        
        # Parse sections
        script = Script(
            topic=topic.title,
            full_text=full_text
        )
        
        script = self._parse_sections(script)
        script.shorts_excerpts = self._extract_shorts(full_text)
        
        logger.info(f"✓ Script generated: {script.word_count} words, ~{script.estimated_duration//60} min")
        
        return script
    
    def _parse_sections(self, script: Script) -> Script:
        """Parse script into sections."""
        text = script.full_text
        
        # Extract sections using headers
        sections = {
            "hook": r"##\s*HOOK.*?\n(.*?)(?=##|$)",
            "overview": r"##\s*OVERVIEW.*?\n(.*?)(?=##|$)",
            "breakdown": r"##\s*DEEP BREAKDOWN.*?\n(.*?)(?=##|$)",
            "implications": r"##\s*IMPLICATIONS.*?\n(.*?)(?=##|$)",
            "conclusion": r"##\s*CONCLUSION.*?\n(.*?)(?=##|$)",
        }
        
        for section_name, pattern in sections.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                setattr(script, section_name, match.group(1).strip())
        
        return script
    
    def _extract_shorts(self, text: str) -> list:
        """Extract Shorts excerpts from script."""
        shorts = []
        
        # Look for Shorts section
        shorts_match = re.search(r"##\s*SHORTS.*?\n(.*?)(?=##|$)", text, re.DOTALL | re.IGNORECASE)
        if shorts_match:
            shorts_text = shorts_match.group(1)
            # Split by numbered items or bullet points
            items = re.split(r'\n\d+\.|\n[-•]', shorts_text)
            shorts = [s.strip() for s in items if len(s.strip()) > 50]
        
        return shorts[:5]  # Max 5 shorts
    
    def generate_hook_variations(self, topic: str, count: int = 5) -> list:
        """Generate multiple hook options for testing."""
        prompt = f"""Generate {count} different viral YouTube video hooks (first 30 seconds) for this topic:

Topic: {topic}

Each hook should be:
- Attention-grabbing and scroll-stopping
- Use different emotional angles (fear, curiosity, urgency, shock)
- About 50-75 words each
- Include a specific statistic or claim when possible

Format as numbered list 1-{count}:"""

        response = self.model.generate_content(prompt)
        hooks = response.text.split('\n')
        return [h.strip() for h in hooks if h.strip() and h[0].isdigit()][:count]


# =============================================================================
# CLI USAGE
# =============================================================================

if __name__ == "__main__":
    from topic_discovery import TopicDiscovery
    
    # Get best topic
    discovery = TopicDiscovery()
    topic = discovery.get_best_topic()
    
    if topic:
        print(f"\n📰 Selected Topic: {topic.title}\n")
        
        # Generate script
        generator = ScriptGenerator()
        script = generator.generate(topic)
        
        print(f"\n{'='*60}")
        print(f"SCRIPT GENERATED")
        print(f"{'='*60}")
        print(f"Words: {script.word_count}")
        print(f"Est. Duration: {script.estimated_duration // 60} min {script.estimated_duration % 60} sec")
        print(f"Shorts: {len(script.shorts_excerpts)}")
        print(f"\n--- HOOK ---\n{script.hook[:300]}...")
    else:
        print("No topics found!")
