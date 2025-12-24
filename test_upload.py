import atexit
import os

import requests

def test_upload():
    url = "http://localhost:8000/upload"
    
    def _cleanup_file() -> None:
        if os.path.exists("test_upload.csv"):
            os.remove("test_upload.csv")

    atexit.register(_cleanup_file)

    with open("test_upload.csv", "w") as f:
        f.write("x,y\n1,2\n3,4")

    with open("test_upload.csv", "rb") as file_handle:
        files = {"file": file_handle}
        print("Sending upload request...")
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Upload successful!")
            print(response.json())
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    test_upload()
