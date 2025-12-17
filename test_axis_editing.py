#!/usr/bin/env python3
"""Test axis editing by simulating user interaction"""
import requests
import json

# First, paste some simple data
data = """x,y
1,2
2,4
3,6
4,8"""

print("1. Pasting data...")
response = requests.post('http://localhost:8000/paste_data', 
    json={'data': data, 'format': 'csv'})
print(f"Status: {response.status_code}")
result = response.json()
file_path = result['path']
print(f"Data saved to: {file_path}")

# Create a simple plot
print("\n2. Creating initial plot...")
response = requests.post('http://localhost:8000/chat',
    json={
        'message': 'Create a scatter plot of x vs y',
        'context': file_path,
        'provider': 'ollama'
    })
result = response.json()
print(f"Plot created: {'plot' in result}")
code = result.get('code', '')
print(f"Code length: {len(code)}")

# Try to change the x-axis label
print("\n3. Testing X-axis label change...")
response = requests.post('http://localhost:8000/chat',
    json={
        'message': 'Change the X-axis label to: Time (seconds)',
        'context': file_path,
        'current_code': code,
        'provider': 'ollama'
    })
result = response.json()
new_code = result.get('code', '')
print(f"New code length: {len(new_code)}")
print(f"Has 'Time (seconds)' in code: {'Time (seconds)' in new_code}")
print(f"\nNew code snippet:")
for line in new_code.split('\n'):
    if 'xlabel' in line.lower() or 'time' in line.lower():
        print(f"  {line}")

# Try to change the y-axis label
print("\n4. Testing Y-axis label change...")
response = requests.post('http://localhost:8000/chat',
    json={
        'message': 'Change the Y-axis label to: Value',
        'context': file_path,
        'current_code': new_code,
        'provider': 'ollama'
    })
result = response.json()
final_code = result.get('code', '')
print(f"Final code length: {len(final_code)}")
print(f"Has 'Value' in code: {'Value' in final_code}")
print(f"\nFinal code snippet:")
for line in final_code.split('\n'):
    if 'ylabel' in line.lower() or 'value' in line.lower():
        print(f"  {line}")
