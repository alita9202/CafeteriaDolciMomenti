from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import pymysql
from flask import current_app


class ReporteTendenciasError(Exception):
    """Raised when trend report data cannot be fetched from MySQL."""


@dataclass
class MySQLConnectionSettings:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str
    connect_timeout: int


class ReporteTendenciasService:
    def __init__(self, settings: MySQLConnectionSettings):
        self.settings = settings

    @classmethod
    def from_current_app(cls) -> "ReporteTendenciasService":
        uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        timeout = int(current_app.config.get("REPORT_DB_TIMEOUT_SECONDS", 8))
        settings = cls._parse_mysql_uri(uri, timeout)
        return cls(settings=settings)

    @staticmethod
    def _parse_mysql_uri(uri: str, timeout: int) -> MySQLConnectionSettings:
        parsed = urlparse(uri)

        if not parsed.scheme.startswith("mysql"):
            raise ReporteTendenciasError(
                "El Reporte 2 requiere una conexion MySQL valida en SQLALCHEMY_DATABASE_URI."
            )

        if not parsed.hostname or not parsed.path:
            raise ReporteTendenciasError("SQLALCHEMY_DATABASE_URI incompleta para MySQL.")

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

    def obtener_datos_reporte_2(self) -> dict[str, Any]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Tendencia de ingresos de los ultimos 6 meses
                    cursor.execute(
                        """
                        SELECT DATE_FORMAT(fecha, '%%Y-%%m') AS mes, COALESCE(SUM(monto), 0) AS ingresos
                        FROM pago
                        WHERE LOWER(estado) IN (%s, %s)
                          AND fecha >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                        GROUP BY DATE_FORMAT(fecha, '%%Y-%%m')
                        ORDER BY mes ASC
                        """,
                        ("completado", "pagado"),
                    )
                    ventas_mensuales_raw = cursor.fetchall()
                    ventas_mensuales = [
                        (row["mes"], float(row["ingresos"] or 0)) for row in ventas_mensuales_raw
                    ]

                    # Horarios con mayor actividad
                    cursor.execute(
                        """
                        SELECT LPAD(HOUR(creado_en), 2, '0') AS hora, COUNT(id) AS cantidad
                        FROM pedido
                        GROUP BY HOUR(creado_en)
                        ORDER BY cantidad DESC
                        LIMIT 8
                        """
                    )
                    actividad_horaria_raw = cursor.fetchall()
                    actividad_horaria = [
                        (f"{row['hora']}:00", int(row["cantidad"]))
                        for row in actividad_horaria_raw
                    ]

                    # Clientes frecuentes
                    cursor.execute(
                        """
                        SELECT c.nombre AS cliente, COUNT(p.id) AS pedidos
                        FROM pedido p
                        INNER JOIN cliente c ON c.id = p.cliente_id
                        GROUP BY c.id, c.nombre
                        ORDER BY pedidos DESC
                        LIMIT 10
                        """
                    )
                    clientes_frecuentes_raw = cursor.fetchall()
                    clientes_frecuentes = [
                        (row["cliente"], int(row["pedidos"])) for row in clientes_frecuentes_raw
                    ]

                    # Comparativa 30 dias actuales vs 30 dias previos
                    cursor.execute(
                        """
                        SELECT COUNT(id) AS pedidos
                        FROM pedido
                        WHERE creado_en >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        """
                    )
                    pedidos_30 = int(cursor.fetchone()["pedidos"] or 0)

                    cursor.execute(
                        """
                        SELECT COUNT(id) AS pedidos
                        FROM pedido
                        WHERE creado_en >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
                          AND creado_en < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        """
                    )
                    pedidos_prev_30 = int(cursor.fetchone()["pedidos"] or 0)

                    cursor.execute(
                        """
                        SELECT COALESCE(SUM(monto), 0) AS ingresos
                        FROM pago
                        WHERE LOWER(estado) IN (%s, %s)
                          AND fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        """,
                        ("completado", "pagado"),
                    )
                    ingresos_30 = float(cursor.fetchone()["ingresos"] or 0)

                    cursor.execute(
                        """
                        SELECT COALESCE(SUM(monto), 0) AS ingresos
                        FROM pago
                        WHERE LOWER(estado) IN (%s, %s)
                          AND fecha >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
                          AND fecha < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        """,
                        ("completado", "pagado"),
                    )
                    ingresos_prev_30 = float(cursor.fetchone()["ingresos"] or 0)

            return {
                "ventas_mensuales": ventas_mensuales,
                "actividad_horaria": actividad_horaria,
                "clientes_frecuentes": clientes_frecuentes,
                "pedidos_30": pedidos_30,
                "pedidos_prev_30": pedidos_prev_30,
                "ingresos_30": ingresos_30,
                "ingresos_prev_30": ingresos_prev_30,
            }
        except Exception as exc:  # noqa: BLE001
            raise ReporteTendenciasError(f"Error consultando MySQL para Reporte 2: {exc}") from exc
