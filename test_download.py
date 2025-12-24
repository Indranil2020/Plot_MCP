import requests
import base64

def test_download():
    url = "http://localhost:8000/download_plot"
    
    # Simple plot code
    code = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y, label='Sine Wave')
plt.title('Test Plot')
plt.legend()
plt.grid(True)
"""

    # Test cases
    test_cases = [
        {"format": "png", "dpi": 72},
        {"format": "png", "dpi": 300},
        {"format": "pdf", "dpi": 300},
        {"format": "svg", "dpi": 300}
    ]

    for case in test_cases:
        print(f"Testing {case['format']} at {case['dpi']} DPI...")
        payload = {
            "code": code,
            "format": case["format"],
            "dpi": case["dpi"]
        }
        
        response = requests.post(url, json=payload, stream=True)
        if response.status_code == 200:
            print(f"  Success! Content-Type: {response.headers.get('Content-Type')}")
            content = response.content
            print(f"  Size: {len(content)} bytes")

            if case["format"] == "png":
                assert content.startswith(b"\x89PNG"), "Invalid PNG header"
            elif case["format"] == "pdf":
                assert content.startswith(b"%PDF"), "Invalid PDF header"
            elif case["format"] == "svg":
                assert b"<svg" in content or b"<?xml" in content, "Invalid SVG content"
        else:
            print(f"  Failed! Status: {response.status_code}")
            print(f"  Response: {response.text}")

if __name__ == "__main__":
    test_download()
