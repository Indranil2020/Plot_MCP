import requests
import json

# Test with space-separated data (like the user described)
space_data = """x y z
1 2 3
4 5 6
7 8 9
10 11 12"""

print("Testing space-separated data...")
response = requests.post('http://localhost:8000/paste_data', 
    json={'data': space_data, 'format': 'csv'})

print("Status:", response.status_code)
result = response.json()
print("\nParsing Info:")
print(json.dumps(result.get('parsing_info', {}), indent=2))
print("\nColumns:", result['analysis']['columns'])
print("Shape:", result['analysis']['shape'])
print("\nSample data:")
print(json.dumps(result.get('parsing_info', {}).get('sample_data', []), indent=2))
