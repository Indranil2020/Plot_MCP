import requests
import json

# Test pasting CSV data
csv_data = """x,y,z
1,2,3
4,5,6
7,8,9"""

response = requests.post('http://localhost:8000/paste_data', 
    json={'data': csv_data, 'format': 'csv'})

print("Status:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))

# Now try to plot with that data
if response.status_code == 200:
    data = response.json()
    file_path = data['path']
    
    # Try to create a plot
    plot_response = requests.post('http://localhost:8000/chat',
        json={
            'message': 'Create a scatter plot of x vs y',
            'context': file_path,
            'provider': 'ollama'
        })
    
    print("\nPlot Status:", plot_response.status_code)
    plot_data = plot_response.json()
    print("Has plot:", 'plot' in plot_data)
    print("Response:", plot_data.get('response', 'No response'))
