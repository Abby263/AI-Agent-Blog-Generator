"""
QA Agent

Performs quality assurance checks on the blog post.
"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.schemas.state import BlogState, QualityReport, QualityIssue
from src.tools.code_validator import CodeValidator


class QAAgent(BaseAgent):
    """Quality assurance agent for validating blog quality."""
    
    def __init__(self):
        """Initialize QA agent."""
        super().__init__("qa")
        self.code_validator = CodeValidator()
    
    def execute(self, state: BlogState) -> Dict[str, Any]:
        """
        Execute quality assurance checks.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with quality report
        """
        self.logger.info("Performing quality assurance checks")
        
        # Perform various quality checks
        technical_accuracy = self._check_technical_accuracy(state)
        completeness = self._check_completeness(state)
        consistency = self._check_consistency(state)
        code_quality = self._check_code_quality(state)
        reference_quality = self._check_reference_quality(state)
        
        # Calculate scores
        category_scores = {
            "technical_accuracy": technical_accuracy["score"],
            "completeness": completeness["score"],
            "consistency": consistency["score"],
            "code_quality": code_quality["score"],
            "reference_quality": reference_quality["score"]
        }
        
        # Calculate overall score (weighted average)
        quality_config = self.config.get_quality_config()
        overall_score = (
            technical_accuracy["score"] * quality_config.get("technical_accuracy", {}).get("weight", 0.3) +
            completeness["score"] * quality_config.get("completeness", {}).get("weight", 0.25) +
            consistency["score"] * quality_config.get("consistency", {}).get("weight", 0.2) +
            code_quality["score"] * quality_config.get("code_quality", {}).get("weight", 0.15) +
            reference_quality["score"] * quality_config.get("reference_quality", {}).get("weight", 0.1)
        )
        
        # Collect issues
        critical_issues = []
        major_issues = []
        minor_issues = []
        
        for check_result in [technical_accuracy, completeness, consistency, code_quality, reference_quality]:
            critical_issues.extend(check_result.get("critical_issues", []))
            major_issues.extend(check_result.get("major_issues", []))
            minor_issues.extend(check_result.get("minor_issues", []))
        
        # Make decision
        thresholds = self.agent_config.get("thresholds", {})
        if len(critical_issues) > 0:
            decision = "reject"
        elif overall_score >= thresholds.get("pass", 9.0):
            decision = "pass"
        elif overall_score >= thresholds.get("minor_revisions", 7.0):
            decision = "pass_with_minor_revisions"
        elif overall_score >= thresholds.get("major_revisions", 5.0):
            decision = "needs_revision"
        else:
            decision = "reject"
        
        quality_report = QualityReport(
            overall_score=overall_score,
            category_scores=category_scores,
            critical_issues=critical_issues,
            major_issues=major_issues,
            minor_issues=minor_issues,
            recommendations=self._generate_recommendations(critical_issues, major_issues, minor_issues),
            decision=decision
        )
        
        self.logger.info(
            f"Quality check completed: score={overall_score:.2f}, decision={decision}"
        )
        
        # Determine next step
        if decision in ["pass", "pass_with_minor_revisions"]:
            next_status = "integrating"
            next_agent = "integration"
        else:
            next_status = "needs_human_review"
            next_agent = "supervisor"
        
        return {
            "quality_report": quality_report,
            "status": next_status,
            "current_agent": next_agent,
            "messages": [
                f"Quality check: {decision} (score: {overall_score:.2f})"
            ]
        }
    
    def _check_technical_accuracy(self, state: BlogState) -> Dict[str, Any]:
        """Check technical accuracy."""
        score = 8.0  # Default score
        issues = {"critical_issues": [], "major_issues": [], "minor_issues": []}
        
        # Check if sections are present
        if len(state.sections) < 8:
            issues["major_issues"].append(QualityIssue(
                section="Overall",
                issue=f"Only {len(state.sections)} sections, expected at least 10",
                severity="major"
            ))
            score -= 1.0
        
        return {"score": score, **issues}
    
    def _check_completeness(self, state: BlogState) -> Dict[str, Any]:
        """Check completeness."""
        score = 10.0
        issues = {"critical_issues": [], "major_issues": [], "minor_issues": []}
        
        # Check sections
        if not state.sections:
            issues["critical_issues"].append(QualityIssue(
                section="Overall",
                issue="No sections generated",
                severity="critical"
            ))
            score = 0.0
        
        # Check outline
        if not state.outline:
            issues["minor_issues"].append(QualityIssue(
                section="Overall",
                issue="No outline created",
                severity="minor"
            ))
            score -= 0.5
        
        # Check references
        if len(state.references) < 10:
            issues["minor_issues"].append(QualityIssue(
                section="References",
                issue=f"Only {len(state.references)} references, expected at least 20",
                severity="minor"
            ))
            score -= 0.5
        
        return {"score": max(0, score), **issues}
    
    def _check_consistency(self, state: BlogState) -> Dict[str, Any]:
        """Check consistency."""
        score = 9.0
        issues = {"critical_issues": [], "major_issues": [], "minor_issues": []}
        
        # Check if all sections have content
        for section in state.sections:
            if not section.content or len(section.content.split()) < 50:
                issues["major_issues"].append(QualityIssue(
                    section=section.title,
                    issue="Section has insufficient content",
                    severity="major"
                ))
                score -= 0.5
        
        return {"score": max(0, score), **issues}
    
    def _check_code_quality(self, state: BlogState) -> Dict[str, Any]:
        """Check code quality."""
        score = 10.0
        issues = {"critical_issues": [], "major_issues": [], "minor_issues": []}
        
        # Validate all code blocks
        for code_block in state.code_blocks:
            validation = self.code_validator.validate_syntax(code_block.code)
            if not validation["valid"]:
                issues["major_issues"].append(QualityIssue(
                    section=code_block.section,
                    issue=f"Code block '{code_block.id}' has syntax errors",
                    severity="major"
                ))
                score -= 1.0
        
        return {"score": max(0, score), **issues}
    
    def _check_reference_quality(self, state: BlogState) -> Dict[str, Any]:
        """Check reference quality."""
        score = 8.0
        issues = {"critical_issues": [], "major_issues": [], "minor_issues": []}
        
        if len(state.references) == 0:
            issues["major_issues"].append(QualityIssue(
                section="References",
                issue="No references provided",
                severity="major"
            ))
            score = 5.0
        
        return {"score": score, **issues}
    
    def _generate_recommendations(
        self,
        critical: List[QualityIssue],
        major: List[QualityIssue],
        minor: List[QualityIssue]
    ) -> List[str]:
        """Generate recommendations based on issues."""
        recommendations = []
        
        if critical:
            recommendations.append("Address all critical issues before proceeding")
        if major:
            recommendations.append(f"Fix {len(major)} major issues to improve quality")
        if minor:
            recommendations.append(f"Consider addressing {len(minor)} minor issues for polish")
        
        if not critical and not major:
            recommendations.append("Content is ready for publication")
        
        return recommendations

