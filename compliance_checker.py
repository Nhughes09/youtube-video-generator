"""
Compliance Checker - Monetization Safety Module
Ensures content is safe for YouTube monetization.

GOALS:
- 100% copyright-safe visuals (stock + AI generated only)
- Original transformative commentary
- No automated upload detection risks
- Human review checkpoints
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass

from config import OUTPUT_DIR, LOGS_DIR
from utils import setup_logger
from visual_sourcer import Visual

logger = setup_logger(__name__)


@dataclass
class ComplianceReport:
    """Compliance check results."""
    passed: bool
    score: int  # 0-100
    visual_safety: str  # safe/warning/risk
    content_originality: str
    monetization_ready: bool
    issues: List[str]
    recommendations: List[str]


class ComplianceChecker:
    """
    Checks content for YouTube monetization compliance.
    
    MONETIZATION REQUIREMENTS:
    1. All visuals must be royalty-free or AI-generated
    2. No copyrighted music
    3. Transformative commentary (fair use support)
    4. No scraped/reuploaded content
    5. Human review before upload
    """
    
    # Safe sources (no copyright issues)
    SAFE_VISUAL_SOURCES = ["pexels", "pixabay", "pollinations", "unsplash", "ai_generated"]
    
    # Risky sources (avoid)
    RISKY_SOURCES = ["youtube", "twitter", "tiktok", "instagram", "unknown"]
    
    def __init__(self):
        self.checks_performed = []
    
    def check_visuals(self, visuals: List[Visual]) -> Tuple[str, List[str]]:
        """Check visual sources for copyright safety."""
        issues = []
        safe_count = 0
        risky_count = 0
        
        for visual in visuals:
            source = visual.source.lower()
            
            if any(safe in source for safe in self.SAFE_VISUAL_SOURCES):
                safe_count += 1
            elif any(risky in source for risky in self.RISKY_SOURCES):
                risky_count += 1
                issues.append(f"Risky visual source: {visual.source} - {visual.id}")
            else:
                # Unknown source - flag for review
                issues.append(f"Unknown source needs review: {visual.source}")
        
        if risky_count > 0:
            status = "risk"
        elif safe_count == len(visuals):
            status = "safe"
        else:
            status = "warning"
        
        return status, issues
    
    def check_script_originality(self, script_text: str) -> Tuple[str, List[str]]:
        """
        Check script for originality markers.
        
        Good indicators:
        - Original analysis language
        - Opinion/commentary phrases
        - Citations/attributions
        """
        issues = []
        originality_score = 0
        
        # Positive indicators (transformative content)
        positive_phrases = [
            "in my analysis", "what this means", "the implications",
            "looking at this", "my take on", "as we can see",
            "this suggests", "the data shows", "according to",
            "experts believe", "studies indicate", "research shows"
        ]
        
        script_lower = script_text.lower()
        
        for phrase in positive_phrases:
            if phrase in script_lower:
                originality_score += 10
        
        # Check length (longer = more original content)
        word_count = len(script_text.split())
        if word_count >= 2000:
            originality_score += 20
        
        # Determine status
        if originality_score >= 50:
            status = "high"
        elif originality_score >= 30:
            status = "medium"
        else:
            status = "low"
            issues.append("Script may lack sufficient original commentary")
        
        return status, issues
    
    def check_monetization_requirements(self) -> Tuple[bool, List[str]]:
        """Check YouTube Partner Program requirements."""
        recommendations = []
        ready = True
        
        # Key requirements for monetization
        recommendations.append("✓ Use only stock footage (Pexels/Pixabay) or AI images (Pollinations)")
        recommendations.append("✓ Add original analysis and commentary throughout")
        recommendations.append("✓ Upload manually to avoid automation detection")
        recommendations.append("✓ Review video fully before making public")
        recommendations.append("✓ Write unique description (not template-only)")
        recommendations.append("✓ Create custom thumbnail through YT Studio")
        
        return ready, recommendations
    
    def run_full_check(
        self,
        visuals: List[Visual] = None,
        script_text: str = "",
        output_dir: Path = None
    ) -> ComplianceReport:
        """
        Run comprehensive compliance check.
        
        Returns detailed report for human review.
        """
        logger.info("🔍 Running compliance check...")
        
        issues = []
        recommendations = []
        scores = []
        
        # 1. Visual safety check
        if visuals:
            visual_status, visual_issues = self.check_visuals(visuals)
            issues.extend(visual_issues)
            scores.append(100 if visual_status == "safe" else 50 if visual_status == "warning" else 20)
        else:
            visual_status = "unknown"
            scores.append(50)
        
        # 2. Script originality check
        if script_text:
            originality_status, originality_issues = self.check_script_originality(script_text)
            issues.extend(originality_issues)
            scores.append(100 if originality_status == "high" else 70 if originality_status == "medium" else 40)
        else:
            originality_status = "unknown"
            scores.append(50)
        
        # 3. Monetization requirements
        monetization_ready, monetization_recs = self.check_monetization_requirements()
        recommendations.extend(monetization_recs)
        
        # Calculate overall score
        overall_score = sum(scores) // len(scores) if scores else 0
        passed = overall_score >= 70 and visual_status != "risk"
        
        report = ComplianceReport(
            passed=passed,
            score=overall_score,
            visual_safety=visual_status,
            content_originality=originality_status if script_text else "unknown",
            monetization_ready=monetization_ready and passed,
            issues=issues,
            recommendations=recommendations
        )
        
        # Log report
        self._log_report(report, output_dir)
        
        return report
    
    def _log_report(self, report: ComplianceReport, output_dir: Path = None):
        """Save compliance report."""
        output_dir = output_dir or OUTPUT_DIR
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "passed": report.passed,
            "score": report.score,
            "visual_safety": report.visual_safety,
            "originality": report.content_originality,
            "monetization_ready": report.monetization_ready,
            "issues": report.issues,
            "recommendations": report.recommendations
        }
        
        report_file = output_dir / f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Console output
        status = "✅ PASSED" if report.passed else "⚠️ REVIEW NEEDED"
        logger.info(f"\n{'='*50}")
        logger.info(f"COMPLIANCE CHECK: {status}")
        logger.info(f"{'='*50}")
        logger.info(f"Score: {report.score}/100")
        logger.info(f"Visual Safety: {report.visual_safety}")
        logger.info(f"Originality: {report.content_originality}")
        logger.info(f"Monetization Ready: {'Yes' if report.monetization_ready else 'Review needed'}")
        
        if report.issues:
            logger.warning("\n⚠️ ISSUES:")
            for issue in report.issues:
                logger.warning(f"  - {issue}")
        
        logger.info(f"\n📄 Report saved: {report_file.name}")


# =============================================================================
# BEST PRACTICES FOR MONETIZATION
# =============================================================================

MONETIZATION_BEST_PRACTICES = """
🎬 YOUTUBE MONETIZATION BEST PRACTICES
=====================================

✅ DO:
1. Use ONLY stock footage from Pexels/Pixabay
2. Use AI-generated images (Pollinations.ai)
3. Add heavy original commentary and analysis
4. Cite sources verbally ("According to...")
5. Upload manually through YouTube Studio
6. Review entire video before publishing
7. Create custom thumbnails in YT Studio
8. Write unique descriptions (not just templates)
9. Wait 24-48 hours between uploads
10. Engage with comments genuinely

❌ DON'T:
1. Download/reupload anyone's content
2. Use copyrighted music
3. Automate the upload process
4. Upload without reviewing
5. Mass upload videso
6. Use clickbait that doesn't deliver
7. Copy scripts from other creators

🔒 FOR MONETIZATION APPROVAL:
- 1,000+ subscribers
- 4,000+ watch hours (12 months)
- No community strikes
- Original, valuable content
- Consistent upload schedule

📝 MANUAL UPLOAD CHECKLIST:
[ ] Review full video
[ ] Check audio quality
[ ] Verify all visuals are stock/AI
[ ] Create custom thumbnail
[ ] Write unique description
[ ] Add proper tags
[ ] Set to "Unlisted" first, then "Public"
[ ] Monitor first 24 hours for any issues
"""


def print_best_practices():
    """Print monetization best practices."""
    print(MONETIZATION_BEST_PRACTICES)


if __name__ == "__main__":
    print_best_practices()
    
    # Example check
    checker = ComplianceChecker()
    
    # Simulate check with mock data
    mock_visuals = [
        type('Visual', (), {'source': 'pexels', 'id': 'test1'})(),
        type('Visual', (), {'source': 'pollinations', 'id': 'test2'})(),
    ]
    
    mock_script = """
    In my analysis of the current AI landscape, what this means for workers is significant.
    According to recent studies, automation is accelerating. The implications are far-reaching.
    As we can see from the data, this trend will continue into 2026 and beyond.
    """
    
    report = checker.run_full_check(mock_visuals, mock_script)
    
    print(f"\n✅ Ready for manual upload: {report.monetization_ready}")
