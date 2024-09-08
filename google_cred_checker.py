import os

# Run this file to check wheather the Google's api key is being authenticated as expected 

key_path = "/Users/suryaae/Radical AI/GeminiQuizzify/auth_key.json"

if os.path.exists(key_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
else:
    raise FileNotFoundError(f"The file {key_path} does not exist.")

from google.auth import credentials
from google.auth.exceptions import DefaultCredentialsError
import google.auth

try:
    credentials, project = google.auth.default()
    print(f"Authenticated with project: {project}")
except DefaultCredentialsError as e:
    print(f"Failed to authenticate: {e}")