"""
Video Assembler Module
Combines visuals, voiceover, and text overlays into final video.
Uses MoviePy for compositing.

ENHANCED LOGGING: Detailed metrics at every step for self-improvement.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import time
import json
from datetime import datetime

from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip,
    TextClip, concatenate_videoclips, CompositeAudioClip
)
from moviepy.config import change_settings
import numpy as np
from PIL import Image

from config import VIDEO_CONFIG, OUTPUT_DIR, TEMP_DIR, LOGS_DIR
from utils import setup_logger, handle_errors, format_timestamp, QualityMetrics
from visual_sourcer import Visual

logger = setup_logger(__name__)


# =============================================================================
# ASSEMBLY METRICS (Exponential Logging for Self-Improvement)
# =============================================================================

class AssemblyMetrics:
    """
    Detailed logging of every assembly step.
    Tracks timing, errors, and quality for pattern learning.
    """
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.start_time = datetime.now()
        self.metrics = {
            "project_id": project_id,
            "started_at": self.start_time.isoformat(),
            "steps": [],
            "errors": [],
            "performance": {},
            "quality_signals": {}
        }
        self.step_count = 0
    
    def log_step(self, step_name: str, details: dict, duration: float = None):
        """Log a processing step with full details."""
        self.step_count += 1
        step_data = {
            "step": self.step_count,
            "name": step_name,
            "timestamp": datetime.now().isoformat(),
            "duration_s": duration,
            "details": details
        }
        self.metrics["steps"].append(step_data)
        logger.info(f"📊 Step {self.step_count}: {step_name} ({duration:.2f}s)" if duration else f"📊 Step {self.step_count}: {step_name}")
    
    def log_error(self, error_type: str, message: str, recoverable: bool = True):
        """Log an error with context."""
        error_data = {
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "recoverable": recoverable,
            "step": self.step_count
        }
        self.metrics["errors"].append(error_data)
        logger.error(f"❌ Error at step {self.step_count}: {error_type} - {message}")
    
    def log_quality_signal(self, signal_name: str, value: any, target: any = None):
        """Log a quality metric for learning."""
        self.metrics["quality_signals"][signal_name] = {
            "value": value,
            "target": target,
            "meets_target": value >= target if target and isinstance(value, (int, float)) else None
        }
    
    def finalize(self, success: bool):
        """Complete metrics logging."""
        self.metrics["completed_at"] = datetime.now().isoformat()
        self.metrics["total_duration_s"] = (datetime.now() - self.start_time).total_seconds()
        self.metrics["success"] = success
        self.metrics["total_steps"] = self.step_count
        self.metrics["total_errors"] = len(self.metrics["errors"])
        
        # Save to log file for pattern learning
        log_file = LOGS_DIR / f"assembly_{self.project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        logger.info(f"📈 Assembly metrics saved: {log_file.name}")
        return self.metrics


# =============================================================================
# VIDEO ASSEMBLER
# =============================================================================

@dataclass
class VideoProject:
    """Represents a video project being assembled."""
    id: str
    title: str
    script_text: str
    visuals: List[Visual] = field(default_factory=list)
    audio_path: Optional[Path] = None
    output_path: Optional[Path] = None
    shorts_paths: List[Path] = field(default_factory=list)
    

class VideoAssembler:
    """
    Assembles final video from components.
    
    Features:
    - Visual sequence with automatic duration matching
    - Text overlays and captions
    - Audio sync with visuals
    - Shorts clip extraction
    - Exponential logging for self-improvement
    """
    
    def __init__(self):
        self.config = VIDEO_CONFIG
        self.output_dir = OUTPUT_DIR
        self.temp_dir = TEMP_DIR / "video_work"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Default text styling
        self.text_style = {
            "font": "Arial-Bold",
            "fontsize": 48,
            "color": "white",
            "stroke_color": "black",
            "stroke_width": 2,
        }
    
    @handle_errors(retry_count=2, fallback=None)
    def _load_visual(self, visual: Visual, target_duration: float) -> Optional[any]:
        """Load a visual as a MoviePy clip."""
        if not visual.local_path or not Path(visual.local_path).exists():
            logger.warning(f"Visual file not found: {visual.local_path}")
            return None
        
        try:
            if visual.type == "video":
                clip = VideoFileClip(visual.local_path)
                # Loop or trim to target duration
                if clip.duration < target_duration:
                    # Loop the video
                    loops = int(target_duration / clip.duration) + 1
                    clip = concatenate_videoclips([clip] * loops)
                clip = clip.subclip(0, target_duration)
            else:
                # Image - create clip with duration
                clip = ImageClip(visual.local_path).set_duration(target_duration)
            
            # Resize to target resolution
            clip = clip.resize(
                newsize=(self.config["width"], self.config["height"])
            )
            
            return clip
            
        except Exception as e:
            logger.error(f"Failed to load visual {visual.id}: {e}")
            return None
    
    def _create_text_overlay(
        self, 
        text: str, 
        duration: float,
        position: str = "bottom",
        style: dict = None
    ) -> TextClip:
        """Create a text overlay clip."""
        style = {**self.text_style, **(style or {})}
        
        txt_clip = TextClip(
            text,
            font=style["font"],
            fontsize=style["fontsize"],
            color=style["color"],
            stroke_color=style["stroke_color"],
            stroke_width=style["stroke_width"],
            method="caption",
            size=(self.config["width"] - 100, None),
            align="center"
        ).set_duration(duration)
        
        # Position
        if position == "bottom":
            txt_clip = txt_clip.set_position(("center", 0.85), relative=True)
        elif position == "top":
            txt_clip = txt_clip.set_position(("center", 0.05), relative=True)
        else:
            txt_clip = txt_clip.set_position(("center", "center"))
        
        return txt_clip
    
    def assemble(
        self,
        project: VideoProject,
        add_captions: bool = True,
        generate_shorts: bool = True
    ) -> VideoProject:
        """
        Assemble final video from all components.
        
        Args:
            project: VideoProject with visuals and audio
            add_captions: Whether to add text captions
            generate_shorts: Whether to extract Shorts clips
            
        Returns:
            Updated VideoProject with output paths
        """
        metrics = AssemblyMetrics(project.id)
        
        try:
            logger.info(f"🎬 Assembling video: {project.title[:50]}...")
            start_time = time.time()
            
            # Step 1: Load audio and get duration
            step_start = time.time()
            audio_clip = AudioFileClip(str(project.audio_path))
            total_duration = audio_clip.duration
            metrics.log_step("load_audio", {
                "duration": total_duration,
                "file": str(project.audio_path)
            }, time.time() - step_start)
            
            metrics.log_quality_signal("audio_duration", total_duration, self.config["min_duration"])
            
            # Step 2: Calculate visual timing
            step_start = time.time()
            num_visuals = len(project.visuals)
            if num_visuals == 0:
                metrics.log_error("no_visuals", "No visuals provided", recoverable=False)
                raise ValueError("No visuals to assemble")
            
            segment_duration = total_duration / num_visuals
            metrics.log_step("calculate_timing", {
                "total_duration": total_duration,
                "num_visuals": num_visuals,
                "segment_duration": segment_duration
            }, time.time() - step_start)
            
            # Step 3: Load and sequence visuals
            step_start = time.time()
            visual_clips = []
            loaded_count = 0
            
            for i, visual in enumerate(project.visuals):
                clip = self._load_visual(visual, segment_duration)
                if clip:
                    visual_clips.append(clip)
                    loaded_count += 1
                else:
                    # Create placeholder (black screen)
                    placeholder = ImageClip(
                        np.zeros((self.config["height"], self.config["width"], 3), dtype=np.uint8)
                    ).set_duration(segment_duration)
                    visual_clips.append(placeholder)
                    metrics.log_error("visual_load_failed", f"Visual {i} failed, using placeholder", recoverable=True)
            
            metrics.log_step("load_visuals", {
                "total": num_visuals,
                "loaded": loaded_count,
                "failed": num_visuals - loaded_count
            }, time.time() - step_start)
            
            metrics.log_quality_signal("visuals_loaded_pct", (loaded_count / num_visuals) * 100, 80)
            
            # Step 4: Concatenate visual sequence
            step_start = time.time()
            video_sequence = concatenate_videoclips(visual_clips, method="compose")
            metrics.log_step("concatenate_visuals", {
                "result_duration": video_sequence.duration
            }, time.time() - step_start)
            
            # Step 5: Add text overlays (optional)
            if add_captions:
                step_start = time.time()
                # Add title card at start
                title_clip = self._create_text_overlay(
                    project.title,
                    duration=5.0,
                    position="center",
                    style={"fontsize": 72}
                )
                
                # Composite title over first 5 seconds
                video_sequence = CompositeVideoClip([
                    video_sequence,
                    title_clip.set_start(0)
                ])
                
                metrics.log_step("add_captions", {
                    "title_duration": 5.0
                }, time.time() - step_start)
            
            # Step 6: Add audio
            step_start = time.time()
            final_video = video_sequence.set_audio(audio_clip)
            metrics.log_step("add_audio", {
                "video_duration": video_sequence.duration,
                "audio_duration": audio_clip.duration
            }, time.time() - step_start)
            
            # Step 7: Render final video
            step_start = time.time()
            output_filename = f"{project.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = self.output_dir / output_filename
            
            logger.info(f"🔄 Rendering video... (this may take a while)")
            final_video.write_videofile(
                str(output_path),
                fps=self.config["fps"],
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                threads=4,
                logger=None  # Suppress moviepy output
            )
            
            project.output_path = output_path
            render_time = time.time() - step_start
            metrics.log_step("render_video", {
                "output_file": str(output_path),
                "file_size_mb": output_path.stat().st_size / (1024*1024)
            }, render_time)
            
            # Step 8: Generate Shorts (optional)
            if generate_shorts:
                step_start = time.time()
                shorts = self._extract_shorts(final_video, project.id)
                project.shorts_paths = shorts
                metrics.log_step("generate_shorts", {
                    "count": len(shorts)
                }, time.time() - step_start)
            
            # Cleanup
            for clip in visual_clips:
                clip.close()
            final_video.close()
            audio_clip.close()
            
            # Final metrics
            total_time = time.time() - start_time
            metrics.log_quality_signal("total_assembly_time", total_time, 300)  # Target < 5 min
            metrics.log_quality_signal("output_duration", video_sequence.duration, self.config["min_duration"])
            
            metrics.finalize(success=True)
            
            logger.info(f"✅ Video assembled successfully!")
            logger.info(f"   Output: {output_path}")
            logger.info(f"   Duration: {format_timestamp(int(video_sequence.duration))}")
            logger.info(f"   Shorts: {len(project.shorts_paths)}")
            logger.info(f"   Time: {total_time:.1f}s")
            
            return project
            
        except Exception as e:
            metrics.log_error("assembly_failed", str(e), recoverable=False)
            metrics.finalize(success=False)
            logger.error(f"❌ Video assembly failed: {e}")
            raise
    
    def _extract_shorts(self, video: any, project_id: str) -> List[Path]:
        """Extract vertical Shorts clips from video."""
        shorts_paths = []
        shorts_dir = self.output_dir / "shorts"
        shorts_dir.mkdir(exist_ok=True)
        
        # Extract clips from key moments
        # Positions: start (hook), middle (key insight), end (conclusion)
        total_duration = video.duration
        clip_positions = [
            (0, min(59, total_duration * 0.03)),  # Hook
            (total_duration * 0.3, total_duration * 0.3 + 59),  # Key point 1
            (total_duration * 0.5, total_duration * 0.5 + 59),  # Middle insight
        ]
        
        for i, (start, end) in enumerate(clip_positions):
            if end > total_duration:
                continue
                
            try:
                short_clip = video.subclip(start, min(end, start + 59))
                
                # Crop to vertical (center crop)
                w, h = short_clip.size
                new_w = int(h * 9 / 16)  # 9:16 aspect ratio
                x1 = (w - new_w) // 2
                short_clip = short_clip.crop(x1=x1, x2=x1+new_w)
                
                # Resize to Shorts dimensions
                short_clip = short_clip.resize(
                    (self.config["shorts_width"], self.config["shorts_height"])
                )
                
                # Export
                short_path = shorts_dir / f"{project_id}_short_{i+1}.mp4"
                short_clip.write_videofile(
                    str(short_path),
                    fps=30,
                    codec="libx264",
                    audio_codec="aac",
                    preset="ultrafast",
                    logger=None
                )
                shorts_paths.append(short_path)
                short_clip.close()
                
            except Exception as e:
                logger.warning(f"Failed to extract short {i+1}: {e}")
        
        return shorts_paths


# =============================================================================
# CLI USAGE
# =============================================================================

if __name__ == "__main__":
    print("Video Assembler module loaded.")
    print("Use VideoAssembler.assemble(project) to create videos.")
    print("All assembly metrics are saved to logs/ for learning.")
