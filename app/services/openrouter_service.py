from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import current_app

from .http_client import HttpClient, HttpClientConfig, HttpClientError


class AIServiceError(Exception):
    """Raised when OpenRouter service cannot provide a valid response."""


@dataclass
class OpenRouterSettings:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int
    max_retries: int
    app_name: str
    app_url: str


class OpenRouterService:
    def __init__(self, settings: OpenRouterSettings, http_client: HttpClient | None = None):
        self.settings = settings
        self.http_client = http_client or HttpClient(
            HttpClientConfig(
                timeout_seconds=settings.timeout_seconds,
                max_retries=settings.max_retries,
            )
        )

    @classmethod
    def from_current_app(cls) -> "OpenRouterService":
        config = current_app.config
        settings = OpenRouterSettings(
            api_key=config.get("OPENROUTER_API_KEY", ""),
            base_url=config.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            model=config.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            timeout_seconds=int(config.get("OPENROUTER_TIMEOUT_SECONDS", 20)),
            max_retries=int(config.get("OPENROUTER_MAX_RETRIES", 2)),
            app_name=config.get("OPENROUTER_APP_NAME", "DolciMomenti"),
            app_url=config.get("OPENROUTER_APP_URL", "http://localhost:8080"),
        )
        return cls(settings=settings)

    @property
    def is_enabled(self) -> bool:
        return bool(self.settings.api_key)

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 400,
    ) -> str:
        if not self.is_enabled:
            raise AIServiceError("OPENROUTER_API_KEY no esta configurada.")

        payload: dict[str, Any] = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "HTTP-Referer": self.settings.app_url,
            "X-Title": self.settings.app_name,
        }

        try:
            response = self.http_client.post_json(
                url=f"{self.settings.base_url}/chat/completions",
                payload=payload,
                headers=headers,
            )
        except HttpClientError as exc:
            raise AIServiceError(f"Error de comunicacion con OpenRouter: {exc}") from exc

        try:
            return response["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise AIServiceError("Respuesta invalida de OpenRouter.") from exc

    def analizar_reporte_general(self, metrics: dict[str, Any]) -> str:
        system_prompt = (
            "Eres un analista de negocio para una cafeteria. "
            "Genera un analisis breve, accionable y en espanol. "
            "Incluye: hallazgos, riesgos y 3 recomendaciones concretas."
        )
        user_prompt = (
            "Analiza estos indicadores del sistema y entrega conclusiones:\n"
            f"{metrics}\n\n"
            "Responde en formato:\n"
            "1) Resumen ejecutivo\n"
            "2) Hallazgos clave\n"
            "3) Recomendaciones"
        )
        return self.chat_completion(system_prompt=system_prompt, user_prompt=user_prompt)

    def analizar_reporte_tendencias(self, metrics: dict[str, Any]) -> str:
        system_prompt = (
            "Eres un analista de comportamiento para una cafeteria. "
            "Detecta patrones de tendencia, cambios relevantes y oportunidades. "
            "Responde en espanol, claro y accionable."
        )
        user_prompt = (
            "Analiza estas metricas de tendencias y comportamiento:\n"
            f"{metrics}\n\n"
            "Estructura la respuesta en:\n"
            "1) Tendencias detectadas\n"
            "2) Alertas o riesgos\n"
            "3) Recomendaciones priorizadas\n"
            "4) Accion sugerida para la siguiente semana"
        )
        return self.chat_completion(system_prompt=system_prompt, user_prompt=user_prompt)

    def analizar_reporte_prediccion(self, metrics: dict[str, Any]) -> str:
        system_prompt = (
            "Eres un consultor senior de operaciones para una cafeteria. "
            "Debes producir recomendaciones accionables de inventario y ventas, "
            "con enfoque en evitar quiebres de stock y mejorar ingresos."
        )
        user_prompt = (
            "Con base en estos datos del sistema, entrega predicciones y recomendaciones:\n"
            f"{metrics}\n\n"
            "Reglas de respuesta:\n"
            "- Usa lenguaje claro en espanol.\n"
            "- Prioriza acciones para los siguientes 7 y 14 dias.\n"
            "- Incluye una lista de productos en riesgo y cantidad sugerida de reposicion.\n"
            "- Cierra con un plan de accion en 5 pasos.\n\n"
            "Formato:\n"
            "1) Prediccion de demanda\n"
            "2) Productos criticos y reposicion sugerida\n"
            "3) Recomendaciones comerciales\n"
            "4) Plan de accion"
        )
        return self.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=600,
        )

    def health_check(self) -> str:
        return self.chat_completion(
            system_prompt="Responde solo con el texto OK_OPENROUTER.",
            user_prompt="Prueba de conectividad.",
            temperature=0,
            max_tokens=20,
        )
