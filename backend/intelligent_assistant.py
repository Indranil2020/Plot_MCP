"""
Advanced Intelligence Module
Handles URL analysis, example extraction, and intelligent plot suggestions
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional

class IntelligentAssistant:
    def __init__(self):
        self.github_pattern = re.compile(r'github\.com/([^/]+)/([^/]+)')
        self.matplotlib_gallery_pattern = re.compile(r'matplotlib\.org/stable/gallery/([^/]+)/([^.]+)\.html')
    
    def analyze_url(self, url: str) -> Dict:
        """Analyze a URL and extract plot information"""
        
        # Check if it's a GitHub repository
        github_match = self.github_pattern.search(url)
        if github_match:
            return self._analyze_github_repo(url, github_match.group(1), github_match.group(2))
        
        # Check if it's a Matplotlib gallery example
        mpl_match = self.matplotlib_gallery_pattern.search(url)
        if mpl_match:
            return self._analyze_matplotlib_example(url, mpl_match.group(1), mpl_match.group(2))
        
        # Try generic URL analysis
        return self._analyze_generic_url(url)
    
    def _analyze_github_repo(self, url: str, owner: str, repo: str) -> Dict:
        """Analyze a GitHub repository for plotting examples"""
        
        # Fetch README
        readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        response = requests.get(readme_url, timeout=10)
        
        if response.status_code != 200:
            # Try master branch
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
            response = requests.get(readme_url, timeout=10)
        
        if response.status_code == 200:
            readme_content = response.text
            
            # Extract plot descriptions and images
            images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', readme_content)
            
            return {
                "type": "github_repo",
                "owner": owner,
                "repo": repo,
                "description": f"GitHub repository: {owner}/{repo}",
                "images": images[:5],  # First 5 images
                "suggestion": f"This appears to be a plotting library/tool. I can help you create similar visualizations. Please describe what specific plot type you'd like to create, or upload your data and I'll suggest appropriate visualizations."
            }
        
        return {
            "type": "github_repo",
            "owner": owner,
            "repo": repo,
            "description": f"GitHub repository: {owner}/{repo}",
            "suggestion": "I can help you create plots similar to this repository. Please describe the visualization you want or upload your data."
        }
            
    
    def _analyze_matplotlib_example(self, url: str, category: str, example: str) -> Dict:
        """Analyze a Matplotlib gallery example"""
        
        return {
            "type": "matplotlib_example",
            "category": category,
            "example": example,
            "suggestion": f"This is a Matplotlib gallery example from the '{category}' category. I have this example in my knowledge base. Would you like me to adapt it to your data?"
        }
    
    def _analyze_generic_url(self, url: str) -> Dict:
        """Analyze a generic URL for plot information"""
        
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract images
        images = soup.find_all('img')
        image_urls = [img.get('src') for img in images[:5] if img.get('src')]
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text() if title else "Unknown"
        
        return {
            "type": "generic_url",
            "title": title_text,
            "images": image_urls,
            "suggestion": f"I found a page titled '{title_text}'. Please describe what kind of plot you'd like to create based on this example, and I'll help you build it with your data."
        }
    
    def generate_suggestion_prompt(self, user_message: str, data_analysis: Optional[Dict] = None) -> str:
        """Generate an intelligent suggestion prompt based on user message and data"""
        
        prompt = ""
        
        # Check if user is asking for help/suggestions
        help_keywords = ['help', 'suggest', 'recommend', 'what should', 'how to', 'ideas', 'unsure', 'don\'t know']
        is_asking_for_help = any(keyword in user_message.lower() for keyword in help_keywords)
        
        if is_asking_for_help and data_analysis:
            prompt += f"""
The user is asking for suggestions. Based on their data:
- Shape: {data_analysis.get('shape', 'unknown')}
- Numeric columns: {', '.join(data_analysis.get('numeric_cols', []))}
- Categorical columns: {', '.join(data_analysis.get('categorical_cols', []))}

Provide 3-5 specific plot suggestions with:
1. Plot type name
2. Which columns to use
3. Why this plot would be insightful for their data
4. A brief example of what they'd learn from it

Be conversational and helpful, not technical.
"""
        
        # Check if user provided a URL
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(user_message)
        
        if urls:
            prompt += f"""
The user provided a URL: {urls[0]}
Acknowledge that you understand they want to create something similar.
Ask them to describe what specific aspect of that example they want to recreate.
Offer to help adapt it to their data.
"""
        
        return prompt

# Global instance
_assistant = None

def get_intelligent_assistant():
    """Get or create the intelligent assistant instance"""
    global _assistant
    if _assistant is None:
        _assistant = IntelligentAssistant()
    return _assistant
