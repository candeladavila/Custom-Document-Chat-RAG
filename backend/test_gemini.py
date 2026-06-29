from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model=model,
    contents="Responde solo con: Gemini funciona correctamente"
)

print(response.text)