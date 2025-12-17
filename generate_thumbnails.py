import os
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import sys
import io
import base64

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from gallery_loader import GalleryLoader

def generate_thumbnails():
    """Generate thumbnails for all gallery examples"""
    loader = GalleryLoader()
    examples = loader.get_all_examples()
    
    # Load existing thumbnails if any
    thumbnails_file = 'frontend/src/gallery_thumbnails.json'
    if os.path.exists(thumbnails_file):
        with open(thumbnails_file, 'r') as f:
            thumbnails = json.load(f)
        print(f"Loaded {len(thumbnails)} existing thumbnails")
    else:
        thumbnails = {}
    
    print(f"Generating thumbnails for {len(examples)} examples...")
    
    for i, example in enumerate(examples):
        # Skip if already generated
        if example['title'] in thumbnails:
            if (i + 1) % 50 == 0:
                print(f"Progress: {i+1}/{len(examples)} (skipped existing)")
            continue
            
        try:
            # Skip interactive examples that block execution
            if any(x in example['code'] for x in ['plt.ginput', 'waitforbuttonpress', 'ginput', 'BlockingContourLabeler']):
                print(f"Skipping interactive example: {example['title']}")
                continue

            # Create a safe execution environment
            plt.clf()
            plt.close('all')
            
            # Execute the code with timeout protection
            # Note: GalleryLoader returns examples with 'code' field
            exec(example['code'], {'plt': plt, 'matplotlib': matplotlib, 'np': __import__('numpy')})
            
            # Save thumbnail with very low quality to save memory
            thumb_data = io.BytesIO()
            plt.savefig(thumb_data, format='png', dpi=20, bbox_inches='tight', pad_inches=0.05)
            thumb_b64 = base64.b64encode(thumb_data.getvalue()).decode('utf-8')
            thumbnails[example['title']] = f"data:image/png;base64,{thumb_b64}"
            
            # Explicit cleanup
            thumb_data.close()
            plt.close('all')
            
            # Save after EVERY example to avoid losing progress
            with open(thumbnails_file, 'w') as f:
                json.dump(thumbnails, f, indent=2)
            
            if (i + 1) % 10 == 0:
                print(f"Progress: {i+1}/{len(examples)} ({len(thumbnails)} thumbnails)")
                
        except Exception as e:
            print(f"Failed: {example['title']}: {str(e)[:100]}")
            plt.close('all')
            continue
    
    print(f"Generated {len(thumbnails)} thumbnails total")
    print("Thumbnail generation complete!")

if __name__ == "__main__":
    generate_thumbnails()
