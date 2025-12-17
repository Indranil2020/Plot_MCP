import json
import base64
import os

try:
    with open('response.json', 'r') as f:
        data = json.load(f)

    if 'plot' in data:
        img_data = base64.b64decode(data['plot'])
        with open('plot.png', 'wb') as f:
            f.write(img_data)
        print("Successfully extracted plot.png")
    else:
        print("No plot data found in response.json")
except Exception as e:
    print(f"Error: {e}")
