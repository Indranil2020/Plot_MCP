#!/usr/bin/env python3
"""
Process ALL Matplotlib gallery examples from the downloaded zip
Creates a comprehensive, production-ready knowledge base
"""

import os
import json
from pathlib import Path

def process_gallery_examples(gallery_dir="gallery_python"):
    """Process all Python examples from the gallery"""
    
    gallery_path = Path(gallery_dir)
    if not gallery_path.exists():
        print(f"Error: {gallery_dir} not found!")
        return {}
    
    all_examples = {}
    total_files = 0
    
    # Get all subdirectories (categories)
    categories = [d for d in gallery_path.iterdir() if d.is_dir()]
    
    print(f"Processing {len(categories)} categories from Matplotlib gallery...")
    print("=" * 70)
    
    for category_dir in sorted(categories):
        category_name = category_dir.name
        print(f"\\n📁 {category_name}")
        
        # Get all Python files in this category
        py_files = list(category_dir.glob("*.py"))
        print(f"   Found {len(py_files)} examples")
        
        category_examples = []
        
        for py_file in sorted(py_files):
            with open(py_file, "r", encoding="utf-8") as f:
                code = f.read()

            title = py_file.stem.replace("_", " ").title()

            category_examples.append(
                {
                    "filename": py_file.name,
                    "title": title,
                    "code": code,
                }
            )

            total_files += 1
        
        all_examples[category_name] = category_examples
        print(f"   ✅ Processed {len(category_examples)} examples")
    
    print("\\n" + "=" * 70)
    print(f"✅ Total: {total_files} examples from {len(categories)} categories")
    
    return all_examples

def create_knowledge_base(examples):
    """Create a structured knowledge base for the LLM"""
    
    knowledge_base = {
        "total_examples": sum(len(cat) for cat in examples.values()),
        "total_categories": len(examples),
        "categories": {}
    }
    
    for category, examples_list in examples.items():
        knowledge_base["categories"][category] = {
            "count": len(examples_list),
            "examples": [
                {
                    "filename": ex["filename"],
                    "title": ex["title"],
                    "code_length": len(ex["code"])
                }
                for ex in examples_list
            ]
        }
    
    return knowledge_base

def main():
    # Process all examples
    examples = process_gallery_examples()
    
    if not examples:
        print("No examples found!")
        return
    
    # Save full examples
    print("\\n💾 Saving examples...")
    with open('backend/matplotlib_gallery_examples_full.json', 'w') as f:
        json.dump(examples, f, indent=2)
    print("   ✅ Saved to: backend/matplotlib_gallery_examples_full.json")
    
    # Create knowledge base summary
    kb = create_knowledge_base(examples)
    with open('backend/matplotlib_gallery_kb.json', 'w') as f:
        json.dump(kb, f, indent=2)
    print("   ✅ Saved knowledge base to: backend/matplotlib_gallery_kb.json")
    
    # Print summary
    print("\\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total Examples: {kb['total_examples']}")
    print(f"Total Categories: {kb['total_categories']}")
    print("\\nCategories:")
    for cat, info in sorted(kb['categories'].items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"  • {cat:40s} {info['count']:3d} examples")
    
    print("\\n✅ Gallery processing complete!")
    print("   The LLM now has access to ALL official Matplotlib examples!")

if __name__ == "__main__":
    main()
