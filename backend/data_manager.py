import pandas as pd
import os
import shutil
import io
from fastapi import UploadFile

class DataManager:
    def __init__(self, upload_dir="uploads"):
        self.upload_dir = upload_dir
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    async def save_file(self, file: UploadFile) -> str:
        """Save uploaded file and return path"""
        file_path = os.path.join(self.upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        return file_path

    async def save_text_data(self, content: str, filename: str) -> str:
        """Save text data (from paste) and return path"""
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path
        return file_path

    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from file into DataFrame"""
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            return pd.read_json(file_path)
        else:
            raise ValueError("Unsupported file format")

    def get_preview(self, file_path):
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            return "Unsupported file format"
        
        return df.head().to_dict(orient='records')

    def get_data_context(self, file_path):
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            return "No data available."
        
        buffer = io.StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()
        
        context = f"""
Data Columns: {list(df.columns)}
Data Types:
{info_str}
First 3 rows:
{df.head(3).to_string()}
"""
        return context
