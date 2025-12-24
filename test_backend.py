import requests
import json

def test_chat():
    url = "http://localhost:8000/chat"
    payload = {
        "message": "Plot a simple sine wave",
        "current_code": "",
        "context": "",
        "provider": "ollama",
        "model": "llama3",
        "api_key": ""
    }
    
    print("Sending request to backend...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Response received:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_chat()
