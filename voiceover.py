"""
Voiceover Module
Text-to-speech using gTTS (free) with optional Google Cloud TTS.
"""

from pathlib import Path
from typing import List, Optional
import re
import time

from gtts import gTTS
from pydub import AudioSegment

from config import GOOGLE_CLOUD_TTS_KEY, TEMP_DIR, VIDEO_CONFIG
from utils import setup_logger, handle_errors, chunk_text

logger = setup_logger(__name__)


class Voiceover:
    """
    Generates voiceover audio from script text.
    
    Uses gTTS (Google Text-to-Speech) - 100% FREE, no API key.
    Optional: Google Cloud TTS for higher quality voices.
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or TEMP_DIR / "audio"
        self.output_dir.mkdir(exist_ok=True)
        
        # Voice settings
        self.lang = "en"
        self.tld = "com"  # US English accent
        
        # Check for Google Cloud TTS (optional premium)
        self.use_cloud_tts = bool(GOOGLE_CLOUD_TTS_KEY)
        if self.use_cloud_tts:
            logger.info("Using Google Cloud TTS (premium voices)")
        else:
            logger.info("Using gTTS (free, good quality)")
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean script text for natural speech."""
        # Remove markdown headers
        text = re.sub(r'#{1,6}\s*', '', text)
        
        # Remove visual cues
        text = re.sub(r'\[VISUAL:[^\]]*\]', '', text, flags=re.IGNORECASE)
        
        # Convert markdown bold/italic to plain
        text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
        
        # Replace [PAUSE] markers with periods for natural pauses
        text = re.sub(r'\[PAUSE\]', '. . .', text, flags=re.IGNORECASE)
        
        # Clean up ellipsis
        text = re.sub(r'\.{3,}', '...', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Clean excess whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    @handle_errors(retry_count=2, retry_delay=2.0)
    def _generate_chunk(self, text: str, output_path: Path) -> Path:
        """Generate audio for a text chunk."""
        tts = gTTS(text=text, lang=self.lang, tld=self.tld, slow=False)
        tts.save(str(output_path))
        return output_path
    
    def generate(self, script_text: str, output_filename: str = "voiceover.mp3") -> Path:
        """
        Generate complete voiceover audio from script.
        
        Args:
            script_text: Full script text
            output_filename: Output filename
            
        Returns:
            Path to generated audio file
        """
        logger.info("🎙️ Generating voiceover...")
        
        # Clean text for speech
        clean_text = self._clean_text_for_speech(script_text)
        
        # Split into chunks (gTTS has limits)
        chunks = chunk_text(clean_text, max_chars=5000)
        logger.info(f"Processing {len(chunks)} audio chunks...")
        
        # Generate audio for each chunk
        chunk_files = []
        for i, chunk in enumerate(chunks):
            chunk_path = self.output_dir / f"chunk_{i:03d}.mp3"
            
            try:
                self._generate_chunk(chunk, chunk_path)
                chunk_files.append(chunk_path)
                logger.debug(f"Generated chunk {i+1}/{len(chunks)}")
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to generate chunk {i}: {e}")
        
        if not chunk_files:
            raise RuntimeError("No audio chunks generated")
        
        # Combine all chunks
        output_path = self.output_dir / output_filename
        combined = self._combine_chunks(chunk_files)
        combined.export(str(output_path), format="mp3")
        
        # Get duration
        duration = len(combined) / 1000  # milliseconds to seconds
        logger.info(f"✓ Voiceover generated: {output_path.name} ({duration:.1f}s)")
        
        # Cleanup chunks
        for chunk_file in chunk_files:
            chunk_file.unlink(missing_ok=True)
        
        return output_path
    
    def _combine_chunks(self, chunk_files: List[Path]) -> AudioSegment:
        """Combine audio chunks with small pauses between."""
        pause = AudioSegment.silent(duration=300)  # 300ms pause
        
        combined = AudioSegment.empty()
        for chunk_file in chunk_files:
            chunk_audio = AudioSegment.from_mp3(str(chunk_file))
            combined += chunk_audio + pause
        
        return combined
    
    def generate_sections(
        self, 
        sections: dict,
        output_dir: Path = None
    ) -> dict:
        """
        Generate separate audio files for each script section.
        Useful for precise timing in video assembly.
        
        Args:
            sections: Dict with section names and text
            
        Returns:
            Dict mapping section names to audio file paths
        """
        output_dir = output_dir or self.output_dir
        audio_files = {}
        
        for section_name, text in sections.items():
            if not text or len(text.strip()) < 10:
                continue
                
            output_path = output_dir / f"{section_name}.mp3"
            try:
                clean_text = self._clean_text_for_speech(text)
                chunks = chunk_text(clean_text, max_chars=5000)
                
                chunk_files = []
                for i, chunk in enumerate(chunks):
                    chunk_path = output_dir / f"{section_name}_chunk_{i}.mp3"
                    self._generate_chunk(chunk, chunk_path)
                    chunk_files.append(chunk_path)
                    time.sleep(0.3)
                
                if chunk_files:
                    combined = self._combine_chunks(chunk_files)
                    combined.export(str(output_path), format="mp3")
                    audio_files[section_name] = output_path
                    
                    # Cleanup
                    for f in chunk_files:
                        f.unlink(missing_ok=True)
                        
            except Exception as e:
                logger.error(f"Failed to generate {section_name}: {e}")
        
        logger.info(f"✓ Generated {len(audio_files)} section audio files")
        return audio_files
    
    def get_duration(self, audio_path: Path) -> float:
        """Get duration of an audio file in seconds."""
        audio = AudioSegment.from_mp3(str(audio_path))
        return len(audio) / 1000


# =============================================================================
# CLI USAGE
# =============================================================================

if __name__ == "__main__":
    voiceover = Voiceover()
    
    test_script = """
    Welcome to this video about artificial intelligence and the future of work.
    
    In 2026, we're witnessing unprecedented changes in the job market.
    
    [PAUSE]
    
    Robots and AI systems are now capable of performing tasks that were once 
    thought to be exclusively human.
    
    Let's dive into the five most important developments you need to know about.
    """
    
    print("🎙️ Testing voiceover generation...")
    audio_path = voiceover.generate(test_script, "test_voiceover.mp3")
    
    duration = voiceover.get_duration(audio_path)
    print(f"✓ Generated: {audio_path}")
    print(f"✓ Duration: {duration:.1f} seconds")
