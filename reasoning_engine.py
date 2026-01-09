"""
Reasoning Engine - Meta-Cognitive Intelligence Layer
Provides self-aware decision-making, pattern learning, and intelligent orchestration.

This module enables:
- Chain-of-thought reasoning for complex decisions
- Pattern recognition from past executions
- Self-improvement through metric analysis
- Intelligent fallback and recovery strategies
- Exponential logging for consciousness-like awareness
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from functools import wraps
import hashlib

from config import LOGS_DIR
from utils import setup_logger

logger = setup_logger("reasoning")


# =============================================================================
# THOUGHT PROCESS LOGGING
# =============================================================================

@dataclass
class Thought:
    """A single thought/reasoning step."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    category: str = ""  # analysis, decision, observation, error, insight
    content: str = ""
    confidence: float = 0.8  # 0-1
    evidence: List[str] = field(default_factory=list)
    alternatives_considered: List[str] = field(default_factory=list)


@dataclass
class ReasoningChain:
    """A complete chain of reasoning for a task."""
    task_id: str
    goal: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    thoughts: List[Thought] = field(default_factory=list)
    decisions_made: List[Dict] = field(default_factory=list)
    patterns_recognized: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    outcome: str = ""
    success: bool = False
    
    def add_thought(self, category: str, content: str, confidence: float = 0.8, 
                    evidence: List[str] = None, alternatives: List[str] = None):
        """Add a thought to the chain."""
        thought = Thought(
            category=category,
            content=content,
            confidence=confidence,
            evidence=evidence or [],
            alternatives_considered=alternatives or []
        )
        self.thoughts.append(thought)
        logger.debug(f"💭 [{category.upper()}] {content}")
        return thought
    
    def add_decision(self, decision: str, reasoning: str, confidence: float = 0.8):
        """Log a decision with reasoning."""
        self.decisions_made.append({
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"🎯 DECISION: {decision}")
        logger.debug(f"   Reasoning: {reasoning}")
    
    def recognize_pattern(self, pattern: str):
        """Log a recognized pattern."""
        self.patterns_recognized.append(pattern)
        logger.info(f"🔍 PATTERN: {pattern}")
    
    def learn_lesson(self, lesson: str):
        """Log a learned lesson."""
        self.lessons_learned.append(lesson)
        logger.info(f"📚 LESSON: {lesson}")


# =============================================================================
# REASONING ENGINE
# =============================================================================

class ReasoningEngine:
    """
    Meta-cognitive intelligence layer.
    Provides structured reasoning, pattern learning, and self-improvement.
    """
    
    def __init__(self, knowledge_path: Path = None):
        self.knowledge_path = knowledge_path or LOGS_DIR / "knowledge"
        self.knowledge_path.mkdir(parents=True, exist_ok=True)
        
        self.current_chain: Optional[ReasoningChain] = None
        self.execution_history: List[Dict] = []
        self.learned_patterns: Dict[str, Dict] = {}
        
        # Load previous knowledge
        self._load_knowledge()
    
    def _load_knowledge(self):
        """Load learned patterns from previous executions."""
        patterns_file = self.knowledge_path / "patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file) as f:
                    self.learned_patterns = json.load(f)
                logger.info(f"📚 Loaded {len(self.learned_patterns)} learned patterns")
            except:
                self.learned_patterns = {}
    
    def _save_knowledge(self):
        """Persist learned knowledge."""
        patterns_file = self.knowledge_path / "patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump(self.learned_patterns, f, indent=2)
    
    # =========================================================================
    # REASONING CHAIN MANAGEMENT
    # =========================================================================
    
    def begin_reasoning(self, task_id: str, goal: str) -> ReasoningChain:
        """Start a new reasoning chain for a task."""
        self.current_chain = ReasoningChain(task_id=task_id, goal=goal)
        
        # Initial analysis thought
        self.think(
            "analysis",
            f"Beginning task: {goal}",
            evidence=["User request received", "Pipeline initialized"]
        )
        
        # Check for relevant patterns
        relevant_patterns = self._find_relevant_patterns(goal)
        if relevant_patterns:
            self.think(
                "insight",
                f"Found {len(relevant_patterns)} relevant patterns from previous executions",
                evidence=relevant_patterns[:3]
            )
        
        logger.info(f"🧠 REASONING CHAIN STARTED: {goal[:50]}...")
        return self.current_chain
    
    def think(self, category: str, content: str, confidence: float = 0.8,
              evidence: List[str] = None, alternatives: List[str] = None) -> Thought:
        """Add a thought to the current reasoning chain."""
        if not self.current_chain:
            self.begin_reasoning("unknown", "Untracked reasoning")
        
        return self.current_chain.add_thought(
            category, content, confidence, evidence, alternatives
        )
    
    def decide(self, decision: str, reasoning: str, confidence: float = 0.8):
        """Make and log a decision."""
        if self.current_chain:
            self.current_chain.add_decision(decision, reasoning, confidence)
    
    def end_reasoning(self, success: bool, outcome: str):
        """Complete the reasoning chain and extract learnings."""
        if not self.current_chain:
            return
        
        self.current_chain.success = success
        self.current_chain.outcome = outcome
        
        # Extract and store learnings
        if success:
            self._extract_success_patterns()
        else:
            self._extract_failure_patterns()
        
        # Save the chain
        chain_file = self.knowledge_path / f"chain_{self.current_chain.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(chain_file, 'w') as f:
            json.dump(asdict(self.current_chain), f, indent=2)
        
        logger.info(f"🧠 REASONING CHAIN COMPLETE: {'✅ Success' if success else '❌ Failed'}")
        self._save_knowledge()
        
        chain = self.current_chain
        self.current_chain = None
        return chain
    
    # =========================================================================
    # PATTERN LEARNING
    # =========================================================================
    
    def _find_relevant_patterns(self, goal: str) -> List[str]:
        """Find patterns relevant to the current goal."""
        relevant = []
        goal_lower = goal.lower()
        
        for pattern_key, pattern_data in self.learned_patterns.items():
            keywords = pattern_data.get("keywords", [])
            if any(kw in goal_lower for kw in keywords):
                relevant.append(pattern_data.get("description", pattern_key))
        
        return relevant
    
    def _extract_success_patterns(self):
        """Extract patterns from successful execution."""
        if not self.current_chain:
            return
        
        # Create pattern signature
        pattern_key = hashlib.md5(self.current_chain.goal.encode()).hexdigest()[:8]
        
        # Extract key decision patterns
        decision_patterns = [d["decision"] for d in self.current_chain.decisions_made]
        
        self.learned_patterns[pattern_key] = {
            "description": f"Successful: {self.current_chain.goal[:50]}",
            "keywords": self.current_chain.goal.lower().split()[:5],
            "successful_decisions": decision_patterns,
            "insights": [t.content for t in self.current_chain.thoughts if t.category == "insight"],
            "timestamp": datetime.now().isoformat(),
            "success_count": self.learned_patterns.get(pattern_key, {}).get("success_count", 0) + 1
        }
        
        self.current_chain.learn_lesson(f"Pattern stored: {pattern_key}")
    
    def _extract_failure_patterns(self):
        """Extract patterns from failed execution."""
        if not self.current_chain:
            return
        
        # Find the error thoughts
        errors = [t for t in self.current_chain.thoughts if t.category == "error"]
        
        if errors:
            error_key = f"avoid_{hashlib.md5(errors[0].content.encode()).hexdigest()[:8]}"
            self.learned_patterns[error_key] = {
                "description": f"Avoid: {errors[0].content[:50]}",
                "keywords": ["error", "fail"] + errors[0].content.lower().split()[:3],
                "failure_context": self.current_chain.goal,
                "error_details": [e.content for e in errors],
                "timestamp": datetime.now().isoformat()
            }
    
    # =========================================================================
    # INTELLIGENT EXECUTION
    # =========================================================================
    
    def analyze_task(self, task_description: str) -> Dict:
        """Analyze a task and return structured insights."""
        self.think("analysis", f"Analyzing task: {task_description[:50]}...")
        
        analysis = {
            "complexity": self._estimate_complexity(task_description),
            "risks": self._identify_risks(task_description),
            "dependencies": self._identify_dependencies(task_description),
            "recommended_approach": self._recommend_approach(task_description),
            "estimated_time": self._estimate_time(task_description)
        }
        
        self.think(
            "observation",
            f"Task complexity: {analysis['complexity']}/10, "
            f"Risks: {len(analysis['risks'])}, "
            f"Est. time: {analysis['estimated_time']}s"
        )
        
        return analysis
    
    def _estimate_complexity(self, task: str) -> int:
        """Estimate task complexity (1-10)."""
        complexity = 5
        
        # Increase for complex keywords
        complex_indicators = ["video", "assembly", "generate", "scrape", "api", "multiple"]
        for indicator in complex_indicators:
            if indicator in task.lower():
                complexity += 1
        
        return min(10, complexity)
    
    def _identify_risks(self, task: str) -> List[str]:
        """Identify potential risks."""
        risks = []
        
        if "api" in task.lower():
            risks.append("API rate limiting or failure")
        if "video" in task.lower():
            risks.append("Long processing time for video rendering")
        if "download" in task.lower():
            risks.append("Network failures during downloads")
        if "scrape" in task.lower():
            risks.append("Website structure changes")
        
        return risks
    
    def _identify_dependencies(self, task: str) -> List[str]:
        """Identify task dependencies."""
        deps = []
        
        if "video" in task.lower():
            deps.extend(["moviepy", "ffmpeg"])
        if "voice" in task.lower() or "audio" in task.lower():
            deps.extend(["gTTS", "pydub"])
        if "image" in task.lower() or "visual" in task.lower():
            deps.extend(["Pillow", "requests"])
        
        return list(set(deps))
    
    def _recommend_approach(self, task: str) -> str:
        """Recommend an approach based on task analysis."""
        # Check learned patterns for successful approaches
        for pattern in self.learned_patterns.values():
            if pattern.get("success_count", 0) > 0:
                keywords = pattern.get("keywords", [])
                if any(kw in task.lower() for kw in keywords):
                    return f"Follow successful pattern: {pattern.get('description', 'Unknown')}"
        
        return "Use default modular approach with error handling"
    
    def _estimate_time(self, task: str) -> int:
        """Estimate execution time in seconds."""
        base_time = 60
        
        if "video" in task.lower():
            base_time += 300  # Video rendering
        if "download" in task.lower():
            base_time += 120  # Downloads
        if "generate" in task.lower():
            base_time += 60  # AI generation
        
        return base_time

    # =========================================================================
    # DECORATOR FOR INTELLIGENT FUNCTION EXECUTION
    # =========================================================================
    
    def intelligent_execute(self, func_name: str = None, fallback: Any = None):
        """
        Decorator that adds reasoning to function execution.
        Logs thoughts before, during, and after execution.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = func_name or func.__name__
                start_time = time.time()
                
                # Pre-execution reasoning
                self.think(
                    "analysis",
                    f"Executing {name} with {len(args)} args, {len(kwargs)} kwargs"
                )
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Post-execution observation
                    self.think(
                        "observation",
                        f"{name} completed successfully in {duration:.2f}s",
                        confidence=0.95
                    )
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Error reasoning
                    self.think(
                        "error",
                        f"{name} failed after {duration:.2f}s: {str(e)}",
                        confidence=0.3
                    )
                    
                    # Decide on recovery
                    if fallback is not None:
                        self.decide(
                            f"Use fallback for {name}",
                            f"Function failed with: {str(e)[:50]}",
                            confidence=0.7
                        )
                        return fallback
                    raise
                    
            return wrapper
        return decorator


# =============================================================================
# GLOBAL REASONING ENGINE INSTANCE
# =============================================================================

# Create global instance for use across modules
reasoning = ReasoningEngine()


def think(category: str, content: str, **kwargs):
    """Quick access to add a thought."""
    reasoning.think(category, content, **kwargs)


def decide(decision: str, reasoning_text: str, confidence: float = 0.8):
    """Quick access to log a decision."""
    reasoning.decide(decision, reasoning_text, confidence)


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    print("🧠 Testing Reasoning Engine...\n")
    
    # Start a reasoning chain
    reasoning.begin_reasoning("test_001", "Generate a test video about AI jobs")
    
    # Simulate reasoning process
    reasoning.think("analysis", "User wants a video about AI jobs")
    reasoning.think("observation", "Topic is trending based on keyword analysis")
    reasoning.decide("Use Gemini for script", "Best free option with high quality")
    reasoning.think("insight", "Previous successful videos used 15-20 min format")
    
    # Analyze a task
    analysis = reasoning.analyze_task("Generate video about robotics and unemployment")
    print(f"\n📊 Task Analysis:")
    print(f"   Complexity: {analysis['complexity']}/10")
    print(f"   Risks: {analysis['risks']}")
    print(f"   Est. Time: {analysis['estimated_time']}s")
    
    # Complete reasoning
    reasoning.end_reasoning(success=True, outcome="Test completed successfully")
    
    print("\n✅ Reasoning Engine operational!")
