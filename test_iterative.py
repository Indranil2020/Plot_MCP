import json
import requests

# First request - create initial plot
first_response = requests.post('http://localhost:8000/chat', json={
    "message": "Create a line plot of x vs y",
    "context": "uploads/test_data.csv",
    "provider": "ollama"
})

first_data = first_response.json()
print("=== FIRST PLOT ===")
print("Plot generated:", "plot" in first_data)
print("Code length:", len(first_data.get('code', '')))

if 'code' in first_data:
    # Second request - edit the plot
    second_response = requests.post('http://localhost:8000/chat', json={
        "message": "Make the lines dashed and add grid",
        "context": "uploads/test_data.csv",
        "current_code": first_data['code'],
        "provider": "ollama"
    })
    
    second_data = second_response.json()
    print("\n=== EDITED PLOT ===")
    print("Plot generated:", "plot" in second_data)
    print("Code length:", len(second_data.get('code', '')))
    print("\nCode diff:")
    print("Has 'linestyle' or 'dashed':", 'linestyle' in second_data.get('code', '') or 'dashed' in second_data.get('code', ''))
    print("Has 'grid':", 'grid' in second_data.get('code', ''))
