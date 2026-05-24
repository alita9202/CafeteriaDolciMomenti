from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import pymysql
from flask import current_app


class ReportePrediccionError(Exception):
    """Raised when prediction/recommendation report data cannot be fetched."""


@dataclass
class MySQLConnectionSettings:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str
    connect_timeout: int


class ReportePrediccionService:
    _cache_data: dict[str, Any] | None = None
    _cache_at: float = 0.0

    def __init__(self, settings: MySQLConnectionSettings, cache_ttl_seconds: int = 180):
        self.settings = settings
        self.cache_ttl_seconds = cache_ttl_seconds

    @classmethod
    def from_current_app(cls) -> "ReportePrediccionService":
        uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        timeout = int(current_app.config.get("REPORT_DB_TIMEOUT_SECONDS", 8))
        cache_ttl = int(current_app.config.get("REPORTE_PREDICCION_CACHE_TTL_SECONDS", 180))
        settings = cls._parse_mysql_uri(uri, timeout)
        return cls(settings=settings, cache_ttl_seconds=cache_ttl)

    @staticmethod
    def _parse_mysql_uri(uri: str, timeout: int) -> MySQLConnectionSettings:
        parsed = urlparse(uri)

        if not parsed.scheme.startswith("mysql"):
            raise ReportePrediccionError(
                "El Reporte 3 requiere una conexion MySQL valida en SQLALCHEMY_DATABASE_URI."
            )

        if not parsed.hostname or not parsed.path:
            raise ReportePrediccionError("SQLALCHEMY_DATABASE_URI incompleta para MySQL.")

        query_params = parse_qs(parsed.query)
        charset = query_params.get("charset", ["utf8mb4"])[0]

        return MySQLConnectionSettings(
            host=parsed.hostname,
            port=int(parsed.port or 3306),
            user=unquote(parsed.username or ""),
            password=unquote(parsed.password or ""),
            database=parsed.path.lstrip("/"),
            charset=charset,
            connect_timeout=timeout,
        )

    def _get_connection(self):
        return pymysql.connect(
            host=self.settings.host,
            port=self.settings.port,
            user=self.settings.user,
            password=self.settings.password,
            database=self.settings.database,
            charset=self.settings.charset,
            connect_timeout=self.settings.connect_timeout,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

    def _is_cache_valid(self) -> bool:
        return self._cache_data is not None and (time.time() - self._cache_at) < self.cache_ttl_seconds

    def obtener_datos_reporte_3(self, force_refresh: bool = False) -> dict[str, Any]:
        if not force_refresh and self._is_cache_valid():
            cached = dict(self._cache_data or {})
            cached["cache_hit"] = True
            cached["cache_age_seconds"] = round(time.time() - self._cache_at, 1)
            return cached

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Producto: ventas 90 dias + stock para sugerencia de reposicion
                    cursor.execute(
                        """
                        SELECT
                            pr.id,
                            pr.nombre,
                            pr.stock,
                            COALESCE(SUM(CASE
                                WHEN pe.creado_en >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
                                AND LOWER(pe.estado) IN (%s, %s)
                                THEN pi.cantidad ELSE 0 END), 0) AS ventas_90d,
                            COALESCE(SUM(CASE
                                WHEN pe.creado_en >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                                AND LOWER(pe.estado) IN (%s, %s)
                                THEN pi.cantidad ELSE 0 END), 0) AS ventas_30d
                        FROM producto pr
                        LEFT JOIN pedido_item pi ON pi.producto_id = pr.id
                        LEFT JOIN pedido pe ON pe.id = pi.pedido_id
                        GROUP BY pr.id, pr.nombre, pr.stock
                        ORDER BY ventas_30d DESC
                        """,
                        ("pagado", "entregado", "pagado", "entregado"),
                    )
                    productos_raw = cursor.fetchall()

                    productos_demanda = []
                    productos_riesgo = []
                    for row in productos_raw:
                        stock = int(row["stock"] or 0)
                        ventas_90d = float(row["ventas_90d"] or 0)
                        ventas_30d = float(row["ventas_30d"] or 0)
                        demanda_diaria = ventas_90d / 90 if ventas_90d > 0 else 0
                        dias_cobertura = (stock / demanda_diaria) if demanda_diaria > 0 else None
                        recomendacion_reposicion = max(0, int((demanda_diaria * 14) - stock))

                        item = {
                            "producto_id": int(row["id"]),
                            "nombre": row["nombre"],
                            "stock": stock,
                            "ventas_90d": round(ventas_90d, 2),
                            "ventas_30d": round(ventas_30d, 2),
                            "demanda_diaria_estimada": round(demanda_diaria, 3),
                            "dias_cobertura": round(dias_cobertura, 1) if dias_cobertura is not None else None,
                            "reposicion_sugerida_14d": recomendacion_reposicion,
                        }
                        productos_demanda.append(item)

                        if demanda_diaria > 0 and dias_cobertura is not None and dias_cobertura <= 10:
                            productos_riesgo.append(item)

                    # Ventas por categoria para priorizar recomendaciones
                    cursor.execute(
                        """
                        SELECT
                            c.nombre AS categoria,
                            COALESCE(SUM(pi.cantidad), 0) AS unidades_30d
                        FROM categoria c
                        LEFT JOIN producto pr ON pr.categoria_id = c.id
                        LEFT JOIN pedido_item pi ON pi.producto_id = pr.id
                        LEFT JOIN pedido pe ON pe.id = pi.pedido_id
                        WHERE pe.id IS NULL
                           OR (
                               pe.creado_en >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                               AND LOWER(pe.estado) IN (%s, %s)
                           )
                        GROUP BY c.id, c.nombre
                        ORDER BY unidades_30d DESC
                        """,
                        ("pagado", "entregado"),
                    )
                    categorias_raw = cursor.fetchall()
                    categorias_top = [
                        {"categoria": row["categoria"], "unidades_30d": int(row["unidades_30d"] or 0)}
                        for row in categorias_raw
                    ]

                    # Resumen de demanda general
                    cursor.execute(
                        """
                        SELECT
                            COALESCE(SUM(CASE
                                WHEN pe.creado_en >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                                AND LOWER(pe.estado) IN (%s, %s)
                                THEN pi.cantidad ELSE 0 END), 0) AS unidades_30d,
                            COALESCE(SUM(CASE
                                WHEN pe.creado_en >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
                                AND LOWER(pe.estado) IN (%s, %s)
                                THEN pi.cantidad ELSE 0 END), 0) AS unidades_90d
                        FROM pedido_item pi
                        LEFT JOIN pedido pe ON pe.id = pi.pedido_id
                        """,
                        ("pagado", "entregado", "pagado", "entregado"),
                    )
                    demanda_general = cursor.fetchone() or {"unidades_30d": 0, "unidades_90d": 0}

            payload = {
                "productos_demanda": sorted(
                    productos_demanda, key=lambda x: x["ventas_30d"], reverse=True
                )[:15],
                "productos_riesgo": sorted(
                    productos_riesgo,
                    key=lambda x: x["dias_cobertura"] if x["dias_cobertura"] is not None else 9999,
                )[:10],
                "categorias_top": categorias_top,
                "demanda_general": {
                    "unidades_30d": float(demanda_general.get("unidades_30d", 0) or 0),
                    "unidades_90d": float(demanda_general.get("unidades_90d", 0) or 0),
                },
                "cache_hit": False,
                "cache_age_seconds": 0,
                "generated_at": int(time.time()),
            }

            self.__class__._cache_data = payload
            self.__class__._cache_at = time.time()
            return payload
        except Exception as exc:  # noqa: BLE001
            raise ReportePrediccionError(f"Error consultando MySQL para Reporte 3: {exc}") from exc
