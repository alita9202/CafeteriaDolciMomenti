from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import pymysql
from flask import current_app


class ReporteGeneralError(Exception):
    """Raised when report data cannot be fetched from MySQL."""


@dataclass
class MySQLConnectionSettings:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str
    connect_timeout: int


class ReporteGeneralService:
    def __init__(self, settings: MySQLConnectionSettings):
        self.settings = settings

    @classmethod
    def from_current_app(cls) -> "ReporteGeneralService":
        uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        timeout = int(current_app.config.get("REPORT_DB_TIMEOUT_SECONDS", 8))
        settings = cls._parse_mysql_uri(uri, timeout)
        return cls(settings=settings)

    @staticmethod
    def _parse_mysql_uri(uri: str, timeout: int) -> MySQLConnectionSettings:
        parsed = urlparse(uri)

        if not parsed.scheme.startswith("mysql"):
            raise ReporteGeneralError(
                "El Reporte 1 requiere una conexion MySQL valida en SQLALCHEMY_DATABASE_URI."
            )

        if not parsed.hostname or not parsed.path:
            raise ReporteGeneralError("SQLALCHEMY_DATABASE_URI incompleta para MySQL.")

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

    def obtener_datos_reporte_1(self) -> dict[str, Any]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS total FROM producto")
                    total_productos = int(cursor.fetchone()["total"])

                    cursor.execute("SELECT COUNT(*) AS total FROM cliente")
                    total_clientes = int(cursor.fetchone()["total"])

                    cursor.execute("SELECT COUNT(*) AS total FROM pedido")
                    total_pedidos = int(cursor.fetchone()["total"])

                    cursor.execute(
                        """
                        SELECT COALESCE(SUM(monto), 0) AS total_vendido
                        FROM pago
                        WHERE LOWER(estado) IN (%s, %s)
                        """,
                        ("completado", "pagado"),
                    )
                    total_vendido = float(cursor.fetchone()["total_vendido"] or 0)

                    cursor.execute(
                        """
                        SELECT LOWER(estado) AS estado, COUNT(id) AS cantidad
                        FROM pedido
                        GROUP BY LOWER(estado)
                        ORDER BY cantidad DESC
                        """
                    )
                    pedidos_por_estado_raw = cursor.fetchall()
                    pedidos_por_estado = [
                        (row["estado"], int(row["cantidad"])) for row in pedidos_por_estado_raw
                    ]

                    cursor.execute(
                        """
                        SELECT pr.nombre AS producto, COALESCE(SUM(pi.cantidad), 0) AS cantidad
                        FROM pedido_item pi
                        INNER JOIN pedido pe ON pe.id = pi.pedido_id
                        INNER JOIN producto pr ON pr.id = pi.producto_id
                        WHERE LOWER(pe.estado) IN (%s, %s)
                        GROUP BY pr.id, pr.nombre
                        ORDER BY cantidad DESC
                        LIMIT 10
                        """,
                        ("pagado", "entregado"),
                    )
                    productos_mas_vendidos_raw = cursor.fetchall()
                    productos_mas_vendidos = [
                        (row["producto"], int(row["cantidad"])) for row in productos_mas_vendidos_raw
                    ]

            return {
                "total_productos": total_productos,
                "total_clientes": total_clientes,
                "total_pedidos": total_pedidos,
                "total_vendido": total_vendido,
                "pedidos_por_estado": pedidos_por_estado,
                "productos_mas_vendidos": productos_mas_vendidos,
            }
        except Exception as exc:  # noqa: BLE001
            raise ReporteGeneralError(f"Error consultando MySQL para Reporte 1: {exc}") from exc
