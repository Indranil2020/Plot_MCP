import requests
import os

def test_upload():
    url = "http://localhost:8000/upload"
    
    # Create a dummy csv
    with open("test_upload.csv", "w") as f:
        f.write("x,y\n1,2\n3,4")
        
    files = {'file': open('test_upload.csv', 'rb')}
    
    try:
        print("Sending upload request...")
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Upload successful!")
            print(response.json())
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        files['file'].close()
        if os.path.exists("test_upload.csv"):
            os.remove("test_upload.csv")

if __name__ == "__main__":
    test_upload()
