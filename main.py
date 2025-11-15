#!/usr/bin/env python3
"""
Main entry point for the AI Agent Blog Series Generator.

Usage:
    python main.py --topic "Real-Time Fraud Detection"
    python main.py --series "ML System Design" --topics "Bot Detection" "ETA Prediction"
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.workflow.graph import run_workflow, run_blog_series
from src.utils.logger import setup_logger, get_logger
from src.utils.config_loader import get_config
from src.schemas.state import BlogSeriesConfig


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Agent Blog Series Generator using LangGraph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate single blog
    python main.py --topic "Real-Time Fraud Detection"
    
    # Generate single blog with requirements
    python main.py --topic "Video Recommendation" --requirements "Scale: 1B users"
    
    # Generate blog series
    python main.py --series "ML System Design" --topics "Bot Detection" "ETA Prediction" "Search Ranking"
    
    # Configure output and author
    python main.py --topic "Fraud Detection" --author "John Doe" --output custom_output/
        """
    )
    
    # Single blog options
    parser.add_argument(
        "--topic",
        type=str,
        help="Blog topic for single blog generation"
    )
    
    parser.add_argument(
        "--requirements",
        type=str,
        default="",
        help="Optional requirements or specifications"
    )
    
    # Blog series options
    parser.add_argument(
        "--series",
        type=str,
        help="Blog series name"
    )
    
    parser.add_argument(
        "--topics",
        nargs="+",
        help="List of topics for blog series"
    )
    
    # General options
    parser.add_argument(
        "--author",
        type=str,
        default="AI Agent",
        help="Author name (default: AI Agent)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory (default: from config)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/workflow_config.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate setup without running workflow"
    )
    
    return parser.parse_args()


def validate_environment() -> bool:
    """
    Validate that required environment variables are set.
    
    Returns:
        True if environment is valid
    """
    import os
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for LLM",
        "TAVILY_API_KEY": "Tavily API key for web search",
    }
    
    optional_vars = {
        "LANGSMITH_API_KEY": "LangSmith API key for tracing (optional)"
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  - {var}: {description}")
    
    if missing:
        print("❌ Missing required environment variables:")
        print("\n".join(missing))
        print("\nPlease set these in your .env file or environment.")
        return False
    
    print("✓ Required environment variables found")
    
    # Check optional vars
    for var, description in optional_vars.items():
        if os.getenv(var):
            print(f"✓ {description} configured")
        else:
            print(f"ℹ {description} not configured (optional)")
    
    return True


def main() -> None:
    """Main execution function."""
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logger(log_level=args.log_level)
    logger.info("=" * 80)
    logger.info("AI Agent Blog Series Generator")
    logger.info("=" * 80)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Load configuration
    try:
        config = get_config(args.config)
        logger.info(f"✓ Configuration loaded from {args.config}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)
    
    # Dry run mode
    if args.dry_run:
        logger.info("✓ Dry run: Environment and configuration validated")
        logger.info("✓ Ready to generate blogs!")
        return
    
    try:
        # Single blog generation
        if args.topic:
            logger.info(f"\nGenerating blog for topic: {args.topic}")
            
            result = run_workflow(
                topic=args.topic,
                requirements=args.requirements,
                author=args.author
            )
            
            if result.get("status") == "completed":
                logger.info("\n" + "=" * 80)
                logger.info("✓ Blog generation completed successfully!")
                logger.info("=" * 80)
                logger.info(f"Topic: {args.topic}")
                logger.info(f"Sections: {len(result.get('sections', []))}")
                logger.info(f"Code examples: {len(result.get('code_blocks', []))}")
                logger.info(f"Diagrams: {len(result.get('diagrams', []))}")
                logger.info(f"References: {len(result.get('references', []))}")
                if result.get('quality_report'):
                    logger.info(f"Quality score: {result['quality_report'].overall_score:.2f}/10")
                logger.info("=" * 80)
            else:
                logger.warning("Blog generation completed with status: {result.get('status')}")
        
        # Blog series generation
        elif args.series and args.topics:
            logger.info(f"\nGenerating blog series: {args.series}")
            logger.info(f"Topics: {', '.join(args.topics)}")
            
            results = run_blog_series(
                topics=args.topics,
                author=args.author
            )
            
            # Summary
            completed = sum(1 for r in results if r["status"] == "completed")
            logger.info("\n" + "=" * 80)
            logger.info("Blog Series Generation Summary")
            logger.info("=" * 80)
            logger.info(f"Series: {args.series}")
            logger.info(f"Total blogs: {len(results)}")
            logger.info(f"Completed: {completed}")
            logger.info(f"Failed: {len(results) - completed}")
            logger.info("=" * 80)
        
        else:
            logger.error("Please provide either --topic for single blog or --series with --topics for series")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\n\nWorkflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nWorkflow failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

