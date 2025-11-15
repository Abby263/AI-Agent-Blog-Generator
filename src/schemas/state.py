"""
Pydantic schemas for workflow state management.

This module defines the state schema used throughout the multi-agent workflow,
ensuring type safety and validation with enhanced features including:
- Series planning capabilities
- Multiple content templates  
- Configurable blog length
- User-provided references
- YouTube video integration
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class RealWorldExample(BaseModel):
    """Real-world implementation example from a company."""
    
    company: str = Field(..., description="Company name (e.g., Netflix, Uber)")
    system: str = Field(..., description="System name")
    scale: str = Field(..., description="Scale metrics")
    latency: Optional[str] = Field(None, description="Latency metrics")
    architecture: str = Field(..., description="Architecture description")
    key_technologies: List[str] = Field(default_factory=list)
    source: str = Field(..., description="Source URL")
    key_insights: List[str] = Field(default_factory=list)


class Statistic(BaseModel):
    """Statistical metric with source."""
    
    metric: str = Field(..., description="Metric name")
    value: str = Field(..., description="Metric value")
    source: str = Field(..., description="Source of the metric")


class ArchitecturePattern(BaseModel):
    """Architecture pattern used in industry."""
    
    pattern: str = Field(..., description="Pattern name")
    used_by: List[str] = Field(..., description="Companies using this pattern")
    benefits: List[str] = Field(..., description="Key benefits")


class YouTubeVideo(BaseModel):
    """YouTube video information."""
    
    title: str = Field(..., description="Video title")
    url: str = Field(..., description="Video URL")
    video_id: str = Field(..., description="YouTube video ID")
    channel: str = Field(..., description="Channel name")
    description: str = Field(default="", description="Video description")
    content_type: Optional[str] = Field(None, description="Content type (tutorial, talk, etc.)")
    key_points: List[str] = Field(default_factory=list, description="Key points from video")
    timestamps: List[Dict[str, str]] = Field(default_factory=list, description="Video timestamps")


class UserReference(BaseModel):
    """User-provided reference source."""
    
    source_name: str = Field(..., description="Name of the source")
    url: Optional[str] = Field(None, description="URL if available")
    description: str = Field(..., description="What this source covers")
    relevance: str = Field(..., description="Why this is relevant")


class ResearchSummary(BaseModel):
    """Research findings summary with enhanced sources."""
    
    real_world_examples: List[RealWorldExample] = Field(default_factory=list)
    statistics: List[Statistic] = Field(default_factory=list)
    engineering_blogs: List[str] = Field(default_factory=list)
    papers: List[Dict[str, str]] = Field(default_factory=list)
    architecture_patterns: List[ArchitecturePattern] = Field(default_factory=list)
    youtube_videos: List[YouTubeVideo] = Field(default_factory=list)
    user_reference_insights: List[Dict[str, Any]] = Field(default_factory=list)


class SectionOutline(BaseModel):
    """Outline for a blog section."""
    
    title: str = Field(..., description="Section title")
    objectives: List[str] = Field(..., description="Section objectives")
    key_points: List[str] = Field(..., description="Key points to cover")
    word_count: int = Field(..., description="Target word count")
    diagrams: List[str] = Field(default_factory=list, description="Diagram IDs")
    code_examples: List[str] = Field(default_factory=list, description="Code example IDs")
    real_world_references: List[str] = Field(default_factory=list)


class BlogOutline(BaseModel):
    """Complete blog outline."""
    
    sections: List[SectionOutline] = Field(..., description="All sections")
    total_words: int = Field(..., description="Total target word count")
    total_diagrams: int = Field(..., description="Total diagrams needed")
    total_code_examples: int = Field(..., description="Total code examples needed")


class SectionContent(BaseModel):
    """Generated section content."""
    
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Markdown content")
    word_count: int = Field(..., description="Actual word count")
    code_placeholders: List[str] = Field(default_factory=list)
    diagram_placeholders: List[str] = Field(default_factory=list)
    citations: List[int] = Field(default_factory=list)


class CodeBlock(BaseModel):
    """Generated code block."""
    
    id: str = Field(..., description="Code block identifier")
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Code content")
    description: str = Field(..., description="Code description")
    section: str = Field(..., description="Section this code belongs to")


class Diagram(BaseModel):
    """Generated diagram."""
    
    id: str = Field(..., description="Diagram identifier")
    type: str = Field(..., description="Diagram type (architecture, flowchart, etc.)")
    mermaid_code: str = Field(..., description="Mermaid diagram code")
    image_path: Optional[str] = Field(None, description="Path to generated PNG")
    description: str = Field(..., description="Diagram description")


class Reference(BaseModel):
    """Citation reference."""
    
    id: int = Field(..., description="Reference number")
    title: str = Field(..., description="Reference title")
    url: str = Field(..., description="Reference URL")
    type: str = Field(..., description="Reference type (blog, paper, doc)")
    accessed_date: Optional[str] = Field(None, description="Date accessed")


class QualityIssue(BaseModel):
    """Quality check issue."""
    
    section: str = Field(..., description="Section with issue")
    issue: str = Field(..., description="Issue description")
    severity: str = Field(..., description="Issue severity (critical, major, minor)")


class QualityReport(BaseModel):
    """Quality assurance report."""
    
    overall_score: float = Field(..., ge=0, le=10, description="Overall quality score")
    category_scores: Dict[str, float] = Field(..., description="Scores by category")
    critical_issues: List[QualityIssue] = Field(default_factory=list)
    major_issues: List[QualityIssue] = Field(default_factory=list)
    minor_issues: List[QualityIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    decision: str = Field(..., description="pass, pass_with_minor_revisions, needs_revision, reject, human_review")


class WorkflowPlan(BaseModel):
    """Supervisor's workflow plan."""
    
    research_priorities: List[str] = Field(..., description="Research priorities")
    focus_areas: List[str] = Field(..., description="Key focus areas")
    critical_sections: List[str] = Field(..., description="Critical sections")
    diagram_types: List[str] = Field(..., description="Required diagram types")
    code_examples_needed: List[str] = Field(..., description="Code examples needed")
    estimated_duration_minutes: int = Field(..., description="Estimated duration")
    checkpoints: List[str] = Field(..., description="Checkpoint locations")


class BlogSeriesPlan(BaseModel):
    """Plan for a blog series."""
    
    series_title: str = Field(..., description="Overall series title")
    blogs: List[Dict[str, Any]] = Field(..., description="List of planned blogs")
    narrative_arc: str = Field(..., description="How the series progresses")
    common_themes: List[str] = Field(..., description="Themes across all blogs")
    cross_references: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Cross-references between blogs"
    )


class ContentConfiguration(BaseModel):
    """Configuration for content generation."""
    
    content_type: str = Field(
        default="blog",
        description="Type of content (blog, news, tutorial, review)"
    )
    template_name: Optional[str] = Field(
        None,
        description="Specific template to use (overrides auto-selection)"
    )
    target_length: int = Field(
        default=8000,
        ge=500,
        le=50000,
        description="Target word count"
    )
    tone: str = Field(
        default="professional",
        description="Writing tone (professional, casual, academic)"
    )
    include_code: bool = Field(
        default=True,
        description="Whether to include code examples"
    )
    include_diagrams: bool = Field(
        default=True,
        description="Whether to include diagrams"
    )
    user_references: List[UserReference] = Field(
        default_factory=list,
        description="User-provided reference sources"
    )


class SeriesConfiguration(BaseModel):
    """Configuration for blog series generation."""
    
    series_name: str = Field(..., description="Name of the blog series")
    number_of_blogs: int = Field(..., ge=1, description="Number of blogs in series")
    topics: List[str] = Field(..., description="Topics for each blog")
    main_topic: str = Field(..., description="Overarching series topic")
    target_audience: str = Field(
        default="Technical professionals",
        description="Target audience"
    )
    content_type: str = Field(
        default="blog",
        description="Content type for all blogs in series"
    )
    maintain_continuity: bool = Field(
        default=True,
        description="Whether to maintain continuity between blogs"
    )
    
    @validator('topics')
    def validate_topics_count(cls, v: List[str], values: Dict[str, Any]) -> List[str]:
        """Validate topics match number_of_blogs."""
        if 'number_of_blogs' in values and len(v) != values['number_of_blogs']:
            raise ValueError(
                f"Number of topics ({len(v)}) must match number_of_blogs ({values['number_of_blogs']})"
            )
        return v


class BlogSeriesConfig(BaseModel):
    """Legacy configuration for generating a blog series (kept for compatibility)."""
    
    series_name: str = Field(..., description="Blog series name")
    number_of_blogs: int = Field(..., ge=1, description="Number of blogs to generate")
    topics: List[str] = Field(..., description="List of blog topics")
    author: str = Field(..., description="Author name")
    output_directory: str = Field(default="output", description="Output directory")
    
    @validator('topics')
    def validate_topics(cls, v: List[str], values: Dict[str, Any]) -> List[str]:
        """Validate that number of topics matches number_of_blogs."""
        if 'number_of_blogs' in values and len(v) != values['number_of_blogs']:
            raise ValueError(
                f"Number of topics ({len(v)}) must match number_of_blogs ({values['number_of_blogs']})"
            )
        return v


class BlogState(BaseModel):
    """
    Main state object for the blog generation workflow.
    
    This state is passed between all agents and accumulates information
    throughout the workflow. Includes enhanced features:
    - Series planning capabilities
    - Multiple content templates
    - Configurable blog length
    - User-provided references
    - YouTube video integration
    """
    
    # Input
    topic: str = Field(..., description="Blog topic")
    requirements: str = Field(default="", description="User requirements")
    focus_areas: List[str] = Field(default_factory=list)
    
    # Enhanced Configuration
    content_config: ContentConfiguration = Field(
        default_factory=ContentConfiguration,
        description="Content generation configuration"
    )
    
    # Series configuration (optional)
    series_config: Optional[SeriesConfiguration] = Field(
        None,
        description="Configuration for series generation"
    )
    
    # Series plan (populated by series planner)
    series_plan: Optional[BlogSeriesPlan] = Field(
        None,
        description="Plan for the blog series"
    )
    
    # Current blog in series
    current_blog_number: Optional[int] = Field(
        None,
        description="Current blog number in series (1-indexed)"
    )
    
    # Previous blogs context (for continuity)
    previous_blogs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Context from previous blogs in series"
    )
    
    # Template information
    selected_template: Optional[str] = Field(
        None,
        description="Selected template name"
    )
    template_sections: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sections from selected template"
    )
    
    # Workflow Management
    workflow_plan: Optional[WorkflowPlan] = Field(None)
    status: str = Field(default="initialized", description="Workflow status")
    current_agent: str = Field(default="supervisor", description="Current agent")
    retry_count: int = Field(default=0, description="Retry counter")
    messages: List[str] = Field(default_factory=list, description="Status messages")
    
    # Research Phase
    research_summary: Optional[ResearchSummary] = Field(None)
    
    # Outline Phase
    outline: Optional[BlogOutline] = Field(None)
    
    # Content Generation Phase
    sections: List[SectionContent] = Field(default_factory=list)
    current_section_index: int = Field(default=0)
    
    # Code Generation Phase
    code_blocks: List[CodeBlock] = Field(default_factory=list)
    
    # Diagram Generation Phase
    diagrams: List[Diagram] = Field(default_factory=list)
    
    # Reference Management
    references: List[Reference] = Field(default_factory=list)
    citations: Dict[str, int] = Field(default_factory=dict)
    
    # Quality Assurance
    quality_report: Optional[QualityReport] = Field(None)
    
    # Final Output
    final_content: str = Field(default="", description="Final markdown content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True
    
    @validator('status')
    def validate_status(cls, v: str) -> str:
        """Validate status field."""
        valid_statuses = [
            "initialized", "series_planning", "researching", "outlining", "writing",
            "generating_code", "generating_diagrams", "referencing",
            "quality_checking", "integrating", "completed", "failed",
            "needs_human_review"
        ]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}")
        return v
    
    def add_message(self, message: str) -> None:
        """Add a status message."""
        self.messages.append(f"[{datetime.now().isoformat()}] {message}")
        self.updated_at = datetime.now()
    
    def update_status(self, status: str, agent: str) -> None:
        """Update workflow status and current agent."""
        self.status = status
        self.current_agent = agent
        self.updated_at = datetime.now()
    
    def is_series_generation(self) -> bool:
        """Check if this is a series generation."""
        return self.series_config is not None
    
    def get_current_blog_title(self) -> str:
        """Get title for current blog in series."""
        if self.series_plan and self.current_blog_number:
            blogs = self.series_plan.blogs
            if 0 < self.current_blog_number <= len(blogs):
                return blogs[self.current_blog_number - 1].get("title", self.topic)
        return self.topic
    
    def get_series_context(self) -> str:
        """Get context string for series continuity."""
        if not self.is_series_generation():
            return ""
        
        context_parts = []
        
        if self.series_plan:
            context_parts.append(
                f"This is blog {self.current_blog_number}/{self.series_config.number_of_blogs} "
                f"in the series: '{self.series_plan.series_title}'"
            )
        
        if self.previous_blogs:
            context_parts.append(
                f"Previous blogs covered: {', '.join([b.get('title', '') for b in self.previous_blogs])}"
            )
        
        if self.series_plan and self.series_plan.common_themes:
            context_parts.append(
                f"Common themes: {', '.join(self.series_plan.common_themes)}"
            )
        
        return " | ".join(context_parts)
    
    def get_target_length(self) -> int:
        """Get target length considering template defaults."""
        if self.content_config:
            return self.content_config.target_length
        return 8000  # Default length