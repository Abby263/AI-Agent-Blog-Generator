"""
YouTube search tool.

Searches YouTube for relevant videos using the YouTube Data API v3.
"""

from typing import List, Dict, Any, Optional
import os
import requests
from src.utils.logger import get_logger
from src.utils.config_loader import get_config

logger = get_logger()


class YouTubeSearchTool:
    """YouTube video search tool."""
    
    def __init__(self):
        """Initialize YouTube search tool."""
        self.logger = get_logger()
        self.config = get_config()
        
        # Get API key (optional - if not provided, will return empty results)
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        
        if not self.api_key:
            self.logger.warning(
                "YOUTUBE_API_KEY not found. YouTube search will be disabled. "
                "Get key from: https://console.cloud.google.com/"
            )
        
        self.base_url = "https://www.googleapis.com/youtube/v3/search"
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        order: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Search YouTube for videos.
        
        Args:
            query: Search query
            max_results: Maximum number of results (default: 5)
            order: Sort order (relevance, date, rating, viewCount)
            
        Returns:
            List of video information dictionaries
        """
        if not self.api_key:
            self.logger.warning("YouTube API key not configured, skipping search")
            return []
        
        self.logger.info(f"Searching YouTube for: {query}")
        
        try:
            # Prepare API request
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "order": order,
                "key": self.api_key,
                "relevanceLanguage": "en"
            }
            
            # Make API request
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract video information
            videos = []
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId", "")
                
                video_info = {
                    "title": snippet.get("title", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "video_id": video_id,
                    "channel": snippet.get("channelTitle", ""),
                    "description": snippet.get("description", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", "")
                }
                videos.append(video_info)
            
            self.logger.info(f"Found {len(videos)} videos for query: {query}")
            return videos
            
        except requests.RequestException as e:
            self.logger.error(f"YouTube API error for query '{query}': {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error in YouTube search: {str(e)}")
            return []
    
    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video details dictionary or None if error
        """
        if not self.api_key:
            return None
        
        try:
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,statistics,contentDetails",
                "id": video_id,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                return None
            
            item = items[0]
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            
            return {
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "description": snippet.get("description", ""),
                "published_at": snippet.get("publishedAt", ""),
                "duration": content_details.get("duration", ""),
                "view_count": statistics.get("viewCount", 0),
                "like_count": statistics.get("likeCount", 0),
                "comment_count": statistics.get("commentCount", 0),
                "tags": snippet.get("tags", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting video details for {video_id}: {str(e)}")
            return None
    
    def search_technical_content(
        self,
        topic: str,
        content_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for technical content related to a topic.
        
        Args:
            topic: Topic to search for
            content_types: Types of content (tutorial, talk, demo, etc.)
            
        Returns:
            List of relevant videos
        """
        if content_types is None:
            content_types = ["tutorial", "talk", "demo", "explanation"]
        
        all_videos = []
        
        for content_type in content_types:
            query = f"{topic} {content_type}"
            videos = self.search(query, max_results=3)
            
            # Add content type to each video
            for video in videos:
                video["content_type"] = content_type
                all_videos.append(video)
        
        # Remove duplicates based on video_id
        seen_ids = set()
        unique_videos = []
        for video in all_videos:
            if video["video_id"] not in seen_ids:
                seen_ids.add(video["video_id"])
                unique_videos.append(video)
        
        return unique_videos
    
    def extract_timestamps(self, description: str) -> List[Dict[str, str]]:
        """
        Extract timestamps from video description.
        
        Args:
            description: Video description text
            
        Returns:
            List of timestamp dictionaries
        """
        import re
        
        # Pattern to match timestamps like "0:00 - Introduction" or "5:30 Topic"
        pattern = r'(\d+:\d+(?::\d+)?)\s*[-–—]?\s*(.+?)(?:\n|$)'
        matches = re.findall(pattern, description)
        
        timestamps = []
        for time, label in matches:
            timestamps.append({
                "time": time,
                "label": label.strip()
            })
        
        return timestamps

