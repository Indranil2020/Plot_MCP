#!/usr/bin/env python3
"""
Batch thumbnail generator for Matplotlib gallery examples.
"""
import base64
import io
import json
import os
import sys

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
from gallery_loader import GalleryLoader

def generate_thumbnails_batch():
    """Generate thumbnails for all gallery examples."""
    loader = GalleryLoader()
    examples = loader.get_all_examples()
    
    # Load existing thumbnails
    thumbnails_file = 'frontend/src/gallery_thumbnails.json'
    if os.path.exists(thumbnails_file):
        with open(thumbnails_file, 'r') as f:
            thumbnails = json.load(f)
        print(f"Loaded {len(thumbnails)} existing thumbnails")
    else:
        thumbnails = {}
    
    print(f"Total examples: {len(examples)}")
    print(f"Remaining: {len(examples) - len(thumbnails)}")
    
    # Skip patterns that cause issues
    skip_patterns = [
        'plt.ginput', 'waitforbuttonpress', 'ginput', 
        'BlockingContourLabeler', 'plt.show()',
        'input(', 'raw_input('
    ]
    
    success_count = 0
    skip_count = 0
    
    for i, example in enumerate(examples):
        title = example['title']
        
        # Skip if already generated
        if title in thumbnails:
            continue
        
        if any(pattern in example["code"] for pattern in skip_patterns):
            print(f"[{i+1}/{len(examples)}] SKIP (interactive): {title}")
            skip_count += 1
            continue

        plt.clf()
        plt.close("all")

        safe_globals = {
            "plt": plt,
            "matplotlib": matplotlib,
            "np": __import__("numpy"),
            "pd": __import__("pandas"),
        }
        exec(example["code"], safe_globals)

        thumb_data = io.BytesIO()
        plt.savefig(thumb_data, format="png", dpi=15, bbox_inches="tight", pad_inches=0.02)
        thumb_b64 = base64.b64encode(thumb_data.getvalue()).decode("utf-8")
        thumbnails[title] = f"data:image/png;base64,{thumb_b64}"

        thumb_data.close()
        plt.close("all")

        success_count += 1

        if success_count % 5 == 0:
            with open(thumbnails_file, "w") as f:
                json.dump(thumbnails, f, indent=2)
            print(f"[{i+1}/{len(examples)}] SAVED: {len(thumbnails)} total ({success_count} new)")
    
    # Final save
    with open(thumbnails_file, 'w') as f:
        json.dump(thumbnails, f, indent=2)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total examples: {len(examples)}")
    print(f"Total thumbnails: {len(thumbnails)}")
    print(f"New successful: {success_count}")
    print(f"Skipped: {skip_count}")
    print(f"Coverage: {len(thumbnails)}/{len(examples)} ({100*len(thumbnails)//len(examples)}%)")

if __name__ == "__main__":
    generate_thumbnails_batch()
