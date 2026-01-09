#!/usr/bin/env python3
"""
AI Video Generator - Main Orchestrator
Complete pipeline for generating 15-20 minute AI/robotics videos.

FEATURES:
- Intelligent reasoning with meta-cognitive awareness
- Exponential logging for self-improvement
- Pattern learning from previous executions
- Modular architecture with graceful fallbacks

USAGE:
    python main.py --topic "AI Mass Layoffs 2026"
    python main.py --discover  # Auto-discover trending topic
    python main.py --test      # Run pipeline test
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

# Local imports
from config import OUTPUT_DIR, GEMINI_API_KEY, PEXELS_API_KEY
from utils import (
    setup_logger, ProgressTracker, QualityMetrics, 
    format_timestamp, sanitize_filename
)
from reasoning_engine import reasoning, think, decide
from topic_discovery import TopicDiscovery, Topic
from script_generator import ScriptGenerator, Script
from visual_sourcer import VisualSourcer
from voiceover import Voiceover
from video_assembler import VideoAssembler, VideoProject
from metadata_generator import MetadataGenerator

logger = setup_logger("main")


class VideoGeneratorPipeline:
    """
    Main orchestrator for the video generation pipeline.
    
    Uses the reasoning engine for intelligent decision-making
    and comprehensive logging for self-improvement.
    """
    
    def __init__(self):
        self.progress = ProgressTracker(total_steps=8)
        self.quality = QualityMetrics()
        
        # Initialize reasoning chain
        reasoning.begin_reasoning(
            task_id=f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            goal="Generate complete YouTube video about AI/robotics"
        )
        
        # Verify API keys
        self._verify_configuration()
    
    def _verify_configuration(self):
        """Verify required configuration is present."""
        think("analysis", "Verifying configuration and API keys")
        
        warnings = []
        
        if not GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY not set - script generation will fail")
        else:
            think("observation", "Gemini API key present ✓")
        
        if not PEXELS_API_KEY:
            warnings.append("PEXELS_API_KEY not set - using Pollinations.ai only for visuals")
            decide(
                "Use AI-generated images only",
                "No stock API keys available",
                confidence=0.8
            )
        else:
            think("observation", "Pexels API key present ✓")
        
        for warning in warnings:
            logger.warning(f"⚠️ {warning}")
    
    def run(
        self,
        topic: str = None,
        auto_discover: bool = False,
        skip_render: bool = False
    ) -> Optional[Path]:
        """
        Run the complete video generation pipeline.
        
        Args:
            topic: Specific topic to generate video about
            auto_discover: Automatically discover trending topic
            skip_render: Skip video rendering (for testing)
            
        Returns:
            Path to generated video, or None if failed
        """
        start_time = time.time()
        project_id = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        think("analysis", f"Starting pipeline run: {project_id}")
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 AI VIDEO GENERATOR PIPELINE")
        logger.info(f"{'='*60}\n")
        
        try:
            # ================================================================
            # STEP 1: TOPIC DISCOVERY
            # ================================================================
            self.progress.step("Topic Discovery")
            think("analysis", "Beginning topic discovery phase")
            
            if auto_discover or not topic:
                decide(
                    "Auto-discover trending topic",
                    "No specific topic provided, will find best trending topic",
                    confidence=0.9
                )
                discovery = TopicDiscovery()
                discovered_topic = discovery.get_best_topic()
                
                if not discovered_topic:
                    think("error", "No topics discovered from news sources")
                    raise RuntimeError("Failed to discover any topics")
                
                topic_obj = discovered_topic
                think("insight", f"Best topic scored {topic_obj.score}: {topic_obj.title[:50]}")
            else:
                # Create topic from provided string
                topic_obj = Topic(
                    id=f"manual_{hash(topic) % 10000}",
                    title=topic,
                    source="manual",
                    url="",
                    published=datetime.now().isoformat(),
                    score=100,
                    keywords_matched=topic.lower().split()[:5]
                )
                think("observation", f"Using provided topic: {topic[:50]}")
            
            self.quality.update(topic=topic_obj.title)
            logger.info(f"📰 Topic: {topic_obj.title}")
            
            # ================================================================
            # STEP 2: SCRIPT GENERATION
            # ================================================================
            self.progress.step("Script Generation")
            think("analysis", "Beginning script generation with Gemini")
            
            script_gen = ScriptGenerator()
            script = script_gen.generate(topic_obj)
            
            if script.word_count < 1500:
                think(
                    "observation",
                    f"Script shorter than optimal ({script.word_count} words)",
                    confidence=0.7
                )
            else:
                think("insight", f"Script meets target length: {script.word_count} words")
            
            self.quality.update(
                script_words=script.word_count,
                estimated_duration=script.estimated_duration
            )
            
            logger.info(f"📝 Script: {script.word_count} words, ~{script.estimated_duration//60} min")
            
            # ================================================================
            # STEP 3: VISUAL SOURCING
            # ================================================================
            self.progress.step("Visual Sourcing")
            think("analysis", "Sourcing visuals from stock + AI generation")
            
            visual_sourcer = VisualSourcer()
            visuals = visual_sourcer.collect_visuals_for_topic(
                topic_obj.title,
                script.full_text,
                target_count=15
            )
            
            think("observation", f"Collected {len(visuals)} visuals")
            
            if len(visuals) < 10:
                decide(
                    "Generate additional AI images",
                    f"Only {len(visuals)} visuals found, need more for 15+ min video",
                    confidence=0.8
                )
                # Generate more AI images
                additional = visual_sourcer.generate_ai_images_from_script(
                    script.full_text,
                    count=15 - len(visuals)
                )
                visuals.extend(additional)
            
            # Download all visuals
            visuals = visual_sourcer.download_all(visuals)
            self.quality.update(visuals_count=len(visuals))
            
            logger.info(f"🎬 Visuals: {len(visuals)} downloaded")
            
            # ================================================================
            # STEP 4: VOICEOVER GENERATION
            # ================================================================
            self.progress.step("Voiceover Generation")
            think("analysis", "Generating voiceover audio with gTTS")
            
            voiceover = Voiceover()
            audio_path = voiceover.generate(script.full_text, f"{project_id}_voice.mp3")
            audio_duration = voiceover.get_duration(audio_path)
            
            think("observation", f"Voiceover duration: {audio_duration:.1f}s")
            self.quality.update(audio_duration=audio_duration)
            
            logger.info(f"🎙️ Voiceover: {format_timestamp(int(audio_duration))}")
            
            # ================================================================
            # STEP 5: VIDEO ASSEMBLY
            # ================================================================
            self.progress.step("Video Assembly")
            
            if skip_render:
                think("decision", "Skipping video render (test mode)")
                logger.info("⏭️ Skipping video render (--skip-render)")
                output_path = None
            else:
                think("analysis", "Beginning video assembly with MoviePy")
                
                # Create video project
                project = VideoProject(
                    id=project_id,
                    title=topic_obj.title,
                    script_text=script.full_text,
                    visuals=visuals,
                    audio_path=audio_path
                )
                
                assembler = VideoAssembler()
                project = assembler.assemble(project, add_captions=True, generate_shorts=True)
                
                think("insight", f"Video rendered: {project.output_path}")
                output_path = project.output_path
            
            # ================================================================
            # STEP 6: METADATA GENERATION
            # ================================================================
            self.progress.step("Metadata Generation")
            think("analysis", "Generating YouTube metadata")
            
            metadata_gen = MetadataGenerator()
            metadata = metadata_gen.generate(script, int(audio_duration))
            
            # Save metadata
            meta_path = OUTPUT_DIR / f"{project_id}_metadata.json"
            metadata.save(meta_path)
            
            think("observation", f"Generated {len(metadata.title_options)} title options")
            logger.info(f"📋 Metadata saved: {meta_path.name}")
            
            # ================================================================
            # STEP 7: SCRIPT EXPORT
            # ================================================================
            self.progress.step("Exporting Assets")
            
            # Save script
            script_path = OUTPUT_DIR / f"{project_id}_script.md"
            with open(script_path, 'w') as f:
                f.write(f"# {topic_obj.title}\n\n")
                f.write(f"**Word Count:** {script.word_count}\n")
                f.write(f"**Estimated Duration:** {format_timestamp(script.estimated_duration)}\n\n")
                f.write("---\n\n")
                f.write(script.full_text)
            
            logger.info(f"📄 Script saved: {script_path.name}")
            
            # ================================================================
            # STEP 8: QUALITY REPORT
            # ================================================================
            self.progress.step("Quality Report")
            
            self.quality.save(OUTPUT_DIR)
            
            # Final summary
            total_time = time.time() - start_time
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ PIPELINE COMPLETE")
            logger.info(f"{'='*60}")
            logger.info(f"   Topic: {topic_obj.title[:50]}...")
            logger.info(f"   Duration: ~{audio_duration//60:.0f} min")
            logger.info(f"   Visuals: {len(visuals)}")
            logger.info(f"   Processing Time: {total_time:.1f}s")
            if output_path:
                logger.info(f"   Output: {output_path}")
            logger.info(f"\n{self.quality.summary()}")
            
            # Log best titles
            logger.info("🎯 TITLE OPTIONS:")
            for i, title in enumerate(metadata.title_options[:5], 1):
                logger.info(f"   {i}. {title}")
            
            # Complete reasoning chain
            reasoning.end_reasoning(
                success=True,
                outcome=f"Generated video: {topic_obj.title[:50]}"
            )
            
            self.progress.complete()
            
            return output_path
            
        except Exception as e:
            think("error", f"Pipeline failed: {str(e)}")
            reasoning.end_reasoning(success=False, outcome=str(e))
            logger.error(f"\n❌ PIPELINE FAILED: {e}")
            raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Video Generator - Create YouTube videos about AI/robotics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --topic "AI Mass Layoffs in 2026"
  python main.py --discover
  python main.py --test
        """
    )
    
    parser.add_argument(
        "--topic", "-t",
        type=str,
        help="Specific topic to generate video about"
    )
    
    parser.add_argument(
        "--discover", "-d",
        action="store_true",
        help="Auto-discover trending topic"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (skip video rendering)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if not args.topic and not args.discover:
        # Default to discovery mode
        args.discover = True
    
    try:
        pipeline = VideoGeneratorPipeline()
        output = pipeline.run(
            topic=args.topic,
            auto_discover=args.discover,
            skip_render=args.test
        )
        
        if output:
            print(f"\n✅ Video created: {output}")
        else:
            print("\n✅ Pipeline completed (video rendering skipped)")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
