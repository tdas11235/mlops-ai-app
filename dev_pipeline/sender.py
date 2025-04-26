import requests
import base64
import json
import os
from dotenv import load_dotenv


load_dotenv()

MODEL_API_PORT = os.getenv("MLFLOW_API_PORT", "5001")
mlflow_url = f'http://127.0.0.1:{MODEL_API_PORT}/invocations'
payload = {
    "instances": [
        {
            "text": "It's a happy day"
        }
    ]
}

headers = {'Content-Type': 'application/json'}

response = requests.post(mlflow_url, data=json.dumps(payload), headers=headers)

if response.status_code == 200:
    print("Prediction: {}".format(response.json()))
else:
    print(f"Error: {response.status_code}, {response.text}")
