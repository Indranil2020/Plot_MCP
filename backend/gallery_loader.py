"""
Matplotlib Gallery Loader - Production System
Provides LLM access to ALL 509 official Matplotlib examples
"""

import json
import random
from pathlib import Path

class GalleryLoader:
    def __init__(self, gallery_file="backend/matplotlib_gallery_examples_full.json"):
        self.gallery_file = gallery_file
        self.examples = self._load_examples()
        self.kb = self._load_kb()
    
    def _load_examples(self):
        """Load all gallery examples"""
        try:
            with open(self.gallery_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {self.gallery_file} not found")
            return {}
    
    def _load_kb(self):
        """Load knowledge base summary"""
        try:
            with open("backend/matplotlib_gallery_kb.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def get_category_examples(self, category, limit=3):
        """Get examples from a specific category"""
        if category not in self.examples:
            return []
        
        examples = self.examples[category]
        # Return up to 'limit' random examples
        return random.sample(examples, min(limit, len(examples)))

    def get_all_examples(self):
        """Get all examples as a flat list"""
        all_examples = []
        for category, examples in self.examples.items():
            for example in examples:
                # Ensure category is included
                example['category'] = category
                all_examples.append(example)
        return all_examples
    
    def search_examples(self, query, limit=5):
        """Search for examples matching a query"""
        query_lower = query.lower()
        matches = []
        
        for category, examples in self.examples.items():
            for example in examples:
                title = example['title'].lower()
                filename = example['filename'].lower()
                
                if query_lower in title or query_lower in filename:
                    matches.append({
                        'category': category,
                        'title': example['title'],
                        'filename': example['filename'],
                        'code': example['code']
                    })
                
                if len(matches) >= limit:
                    break
            
            if len(matches) >= limit:
                break
        
        return matches
    
    def get_prompt_summary(self):
        """Get a summary for the LLM prompt"""
        if not self.kb:
            return "Matplotlib gallery examples available."
        
        total = self.kb.get('total_examples', 0)
        categories = self.kb.get('total_categories', 0)
        
        summary = f"""
### OFFICIAL MATPLOTLIB GALLERY - {total} EXAMPLES

You have access to {total} official Matplotlib examples from {categories} categories:

**Major Categories**:
- **Lines, Bars & Markers** (48 examples): Line plots, scatter, bar charts, stem, step, fill_between
- **Images, Contours & Fields** (47 examples): Heatmaps, contour plots, quiver, streamplot, imshow
- **Text, Labels & Annotations** (47 examples): Text boxes, arrows, LaTeX math, annotations
- **3D Plotting** (46 examples): 3D scatter, surface, wireframe, bar, contour
- **Subplots & Figures** (35 examples): GridSpec, insets, shared axes, complex layouts
- **Statistics** (21 examples): Histograms, box plots, violin plots, error bars, hexbin
- **Shapes & Collections** (17 examples): Circles, rectangles, polygons, patches
- **Specialty Plots** (12 examples): Sankey, broken axis, tables, custom plots
- **Pie & Polar Charts** (9 examples): Pie, donut, polar, radar charts
- **Scales** (8 examples): Log, symlog, custom scales
- **Color** (10 examples): Colormaps, color cycles, normalization
- **Animation** (15 examples): Animated plots, dynamic updates
- **Widgets** (17 examples): Interactive elements, sliders, buttons

**Plus**: Ticks (23), Spines (5), Units (10), Style Sheets (8), Event Handling (21), and more!

**How to Use**:
- For ANY plot type, you can reference the official gallery examples
- All examples are production-tested and working
- Adapt examples to the user's data and requirements
- Combine multiple techniques for complex visualizations

**Important**: Always adapt examples to work with the user's DataFrame 'df' and their specific data.
"""
        return summary

# Global instance
_gallery_loader = None

def get_gallery_loader():
    """Get or create the gallery loader instance"""
    global _gallery_loader
    if _gallery_loader is None:
        _gallery_loader = GalleryLoader()
    return _gallery_loader

def get_gallery_prompt():
    """Get the gallery prompt for LLM"""
    loader = get_gallery_loader()
    return loader.get_prompt_summary()
