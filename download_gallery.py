#!/usr/bin/env python3
"""
Download and process ALL Matplotlib gallery examples
Creates a comprehensive knowledge base for the LLM
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re

# All gallery categories from matplotlib.org/stable/gallery/
GALLERY_CATEGORIES = {
    "lines_bars_and_markers": "https://matplotlib.org/stable/gallery/lines_bars_and_markers/index.html",
    "images_contours_and_fields": "https://matplotlib.org/stable/gallery/images_contours_and_fields/index.html",
    "subplots_axes_and_figures": "https://matplotlib.org/stable/gallery/subplots_axes_and_figures/index.html",
    "statistics": "https://matplotlib.org/stable/gallery/statistics/index.html",
    "pie_and_polar_charts": "https://matplotlib.org/stable/gallery/pie_and_polar_charts/index.html",
    "text_labels_and_annotations": "https://matplotlib.org/stable/gallery/text_labels_and_annotations/index.html",
    "color": "https://matplotlib.org/stable/gallery/color/index.html",
    "shapes_and_collections": "https://matplotlib.org/stable/gallery/shapes_and_collections/index.html",
    "style_sheets": "https://matplotlib.org/stable/gallery/style_sheets/index.html",
    "mplot3d": "https://matplotlib.org/stable/gallery/mplot3d/index.html",
    "scales": "https://matplotlib.org/stable/gallery/scales/index.html",
    "specialty_plots": "https://matplotlib.org/stable/gallery/specialty_plots/index.html",
    "ticks": "https://matplotlib.org/stable/gallery/ticks/index.html",
    "spines": "https://matplotlib.org/stable/gallery/spines/index.html",
    "units": "https://matplotlib.org/stable/gallery/units/index.html",
    "widgets": "https://matplotlib.org/stable/gallery/widgets/index.html",
}

def fetch_example_links(category_url):
    """Fetch all example links from a category page"""
    try:
        response = requests.get(category_url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all example links
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.html') and not href.endswith('index.html'):
                full_url = f"https://matplotlib.org/stable/gallery/{href.split('/')[-2]}/{href.split('/')[-1]}"
                links.append({
                    'title': link.get_text(strip=True),
                    'url': full_url
                })
        
        return links
    except Exception as e:
        print(f"Error fetching {category_url}: {e}")
        return []

def extract_code_from_example(example_url):
    """Extract Python code from an example page"""
    try:
        response = requests.get(example_url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find code blocks
        code_blocks = soup.find_all('div', class_='highlight-python')
        if not code_blocks:
            code_blocks = soup.find_all('pre')
        
        code = ""
        for block in code_blocks:
            code_text = block.get_text()
            # Clean up the code
            code_text = re.sub(r'^>>>\\s*', '', code_text, flags=re.MULTILINE)
            code_text = re.sub(r'^\\.\\.\\. ', '', code_text, flags=re.MULTILINE)
            code += code_text + "\\n"
        
        return code.strip()
    except Exception as e:
        print(f"Error extracting code from {example_url}: {e}")
        return ""

def main():
    """Download all examples and create knowledge base"""
    all_examples = {}
    
    print("Downloading Matplotlib Gallery Examples...")
    print("=" * 60)
    
    for category, url in GALLERY_CATEGORIES.items():
        print(f"\\nProcessing category: {category}")
        print(f"URL: {url}")
        
        # Fetch example links
        links = fetch_example_links(url)
        print(f"Found {len(links)} examples")
        
        category_examples = []
        for i, link in enumerate(links[:5]):  # Limit to 5 per category for now
            print(f"  [{i+1}/{min(5, len(links))}] {link['title']}")
            code = extract_code_from_example(link['url'])
            
            if code:
                category_examples.append({
                    'title': link['title'],
                    'url': link['url'],
                    'code': code
                })
            
            time.sleep(0.5)  # Be respectful to the server
        
        all_examples[category] = category_examples
    
    # Save to JSON
    with open('matplotlib_gallery_examples.json', 'w') as f:
        json.dump(all_examples, f, indent=2)
    
    print("\\n" + "=" * 60)
    print(f"Downloaded examples from {len(GALLERY_CATEGORIES)} categories")
    print("Saved to: matplotlib_gallery_examples.json")
    
    # Generate summary
    total_examples = sum(len(examples) for examples in all_examples.values())
    print(f"Total examples: {total_examples}")

if __name__ == "__main__":
    main()
