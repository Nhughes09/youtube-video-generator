"""
Utilities - Logging, error handling, and helpers
Reusable across all modules.
"""

import logging
import sys
import time
import json
import hashlib
from functools import wraps
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime
from pathlib import Path
from config import LOG_CONFIG, LOGS_DIR


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logger(name: str) -> logging.Logger:
    """Create a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_CONFIG["level"]))
    
    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(LOG_CONFIG["file"])
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(LOG_CONFIG["format"]))
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger


# =============================================================================
# ERROR HANDLING DECORATOR
# =============================================================================

def handle_errors(
    retry_count: int = 3,
    retry_delay: float = 1.0,
    fallback: Optional[Any] = None,
    log_errors: bool = True
):
    """
    Decorator for automatic error handling with retries.
    Uses exponential backoff.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            
            for attempt in range(retry_count):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"✓ {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                    
                except Exception as e:
                    if log_errors:
                        logger.error(
                            f"✗ Error in {func.__name__} (attempt {attempt + 1}/{retry_count}): {str(e)}"
                        )
                    
                    if attempt < retry_count - 1:
                        sleep_time = retry_delay * (2 ** attempt)
                        time.sleep(sleep_time)
                    else:
                        if fallback is not None:
                            logger.warning(f"↩ Using fallback for {func.__name__}")
                            return fallback
                        raise
            
        return wrapper
    return decorator


# =============================================================================
# DATA HELPERS
# =============================================================================

def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely parse JSON with fallback."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def generate_id(content: str) -> str:
    """Generate a unique ID from content."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def sanitize_filename(name: str) -> str:
    """Make a string safe for use as filename."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name[:100]  # Limit length


def chunk_text(text: str, max_chars: int = 5000) -> List[str]:
    """Split text into chunks for API limits."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_len = 0
    
    for word in words:
        if current_len + len(word) + 1 > max_chars:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_len = len(word)
        else:
            current_chunk.append(word)
            current_len += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def estimate_duration(word_count: int, wpm: int = 150) -> int:
    """Estimate video duration from word count."""
    return int((word_count / wpm) * 60)


def format_timestamp(seconds: int) -> str:
    """Convert seconds to MM:SS or HH:MM:SS format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


# =============================================================================
# PROGRESS TRACKING
# =============================================================================

class ProgressTracker:
    """Track and display pipeline progress."""
    
    def __init__(self, total_steps: int = 7):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()
        self.logger = setup_logger("progress")
    
    def step(self, message: str):
        """Log a progress step."""
        self.current_step += 1
        pct = int((self.current_step / self.total_steps) * 100)
        self.logger.info(f"[{self.current_step}/{self.total_steps}] ({pct}%) {message}")
    
    def complete(self):
        """Log completion."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.logger.info(f"✅ Pipeline complete in {elapsed:.1f}s")


# =============================================================================
# QUALITY METRICS
# =============================================================================

class QualityMetrics:
    """Track and log video quality metrics."""
    
    def __init__(self):
        self.metrics = {
            "created_at": datetime.now().isoformat(),
            "topic": "",
            "script_words": 0,
            "estimated_duration": 0,
            "visuals_count": 0,
            "audio_duration": 0,
            "risk_score": 0,  # 0-100, lower is better
            "viral_score": 0,  # 0-100, higher is better
            "retention_estimate": 0,  # 0-100
        }
        self.logger = setup_logger("quality")
    
    def update(self, **kwargs):
        """Update metrics."""
        self.metrics.update(kwargs)
    
    def calculate_scores(self):
        """Calculate quality scores."""
        # Risk score (all stock footage = low risk)
        self.metrics["risk_score"] = 10  # Very low risk with stock footage only
        
        # Viral score based on script analysis
        words = self.metrics.get("script_words", 0)
        duration = self.metrics.get("estimated_duration", 0)
        
        # Good length for mid-roll ads
        if 840 <= duration <= 1200:
            self.metrics["viral_score"] += 30
        
        # Good word count for engagement
        if 2000 <= words <= 2700:
            self.metrics["viral_score"] += 20
        
        # Sufficient visuals
        if self.metrics.get("visuals_count", 0) >= 10:
            self.metrics["viral_score"] += 20
        
        # Retention estimate based on structure
        self.metrics["retention_estimate"] = min(70, 40 + (words // 100))
    
    def save(self, output_path: Path):
        """Save metrics to JSON."""
        self.calculate_scores()
        metrics_file = output_path / "quality_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        self.logger.info(f"Quality metrics saved: {metrics_file}")
    
    def summary(self) -> str:
        """Get human-readable summary."""
        self.calculate_scores()
        return f"""
📊 Quality Report:
   Duration: ~{format_timestamp(self.metrics['estimated_duration'])}
   Words: {self.metrics['script_words']}
   Visuals: {self.metrics['visuals_count']}
   Risk Score: {self.metrics['risk_score']}/100 (lower=safer)
   Viral Score: {self.metrics['viral_score']}/100
   Retention Est: {self.metrics['retention_estimate']}%
"""
