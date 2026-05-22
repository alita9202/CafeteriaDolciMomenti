import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "deepseek/deepseek-chat-v3-0324:free"
)


def generar_analisis_ia(prompt_usuario):
    """
    Envía un prompt a OpenRouter y devuelve una respuesta generada por IA.
    """

    if not OPENROUTER_API_KEY:
        return "No se encontró la API Key de OpenRouter. Verifica el archivo .env."

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://127.0.0.1:5000",
        "X-Title": "DOLCIMOMENTI"
    }

    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un asistente experto en análisis de datos para una heladería-cafetería. "
                    "Responde siempre en español, de forma clara, breve y útil. "
                    "Da conclusiones y recomendaciones prácticas para mejorar el negocio."
                )
            },
            {
                "role": "user",
                "content": prompt_usuario
            }
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )

        response.raise_for_status()
        resultado = response.json()

        return resultado["choices"][0]["message"]["content"]

    except Exception as error:
        return f"No se pudo generar el análisis con IA. Error: {error}"