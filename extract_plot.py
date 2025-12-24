import base64
import json
import os

if not os.path.exists("response.json"):
    print("response.json not found")
    raise SystemExit(1)

with open("response.json", "r") as f:
    data = json.load(f)

if "plot" in data:
    img_data = base64.b64decode(data["plot"])
    with open("plot.png", "wb") as f:
        f.write(img_data)
    print("Successfully extracted plot.png")
else:
    print("No plot data found in response.json")
