# Importamos las herramientas para conectar Python con PostgreSQL.
import os
import hashlib
import json

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values


# Leemos las credenciales guardadas en el archivo .env.
load_dotenv()


def generar_clave(fila):
    """Genera una clave repetible para evitar cargas duplicadas."""

    valores = [
        str(fila.get("factura", "")),
        str(fila.get("producto", "")),
        str(fila.get("descripcion", "")),
        str(fila.get("cantidad", "")),
        str(fila.get("fecha", "")),
        str(fila.get("precio", "")),
        str(fila.get("cliente", "")),
        str(fila.get("pais", "")),
        str(fila.get("tipo_movimiento", "")),
    ]

    contenido = "|".join(valores)

    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


def limpiar_valor(valor):
    """Convierte valores vacíos de pandas en NULL de PostgreSQL."""

    if pd.isna(valor):
        return None

    return valor


def cargar_ventas(ventas_validas, ventas_rechazadas, fuente):
    """Guarda las ventas válidas y los rechazos en PostgreSQL."""

    conexion = psycopg2.connect(
        host=os.getenv("WAREHOUSE_DB_HOST", "localhost"),
        port=os.getenv("WAREHOUSE_DB_PORT", "5544"),
        dbname=os.getenv("WAREHOUSE_DB_NAME"),
        user=os.getenv("WAREHOUSE_DB_USER"),
        password=os.getenv("WAREHOUSE_DB_PASSWORD"),
    )

    try:
        with conexion:
            with conexion.cursor() as cursor:

                # Preparamos las ventas para insertarlas en una sola operación.
                registros_validos = []

                for fila in ventas_validas.to_dict("records"):
                    cliente = limpiar_valor(fila["cliente"])

                    # Los identificadores de cliente no deben terminar en .0.
                    if cliente is not None:
                        cliente = str(cliente).removesuffix(".0")

                    registros_validos.append((
                        generar_clave(fila),
                        fila["factura"],
                        fila["producto"],
                        limpiar_valor(fila["descripcion"]),
                        float(fila["cantidad"]),
                        fila["fecha"].to_pydatetime(),
                        float(fila["precio"]),
                        cliente,
                        limpiar_valor(fila["pais"]),
                        fila["tipo_movimiento"],
                        float(fila["total"]),
                        fuente,
                    ))

                if registros_validos:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO ventas (
                            clave_registro, factura, producto, descripcion,
                            cantidad, fecha, precio, cliente, pais,
                            tipo_movimiento, total, fuente
                        )
                        VALUES %s
                        ON CONFLICT (clave_registro) DO NOTHING
                        """,
                        registros_validos,
                        page_size=1000,
                    )

                # Guardamos también los registros que no pasaron la validación.
                registros_rechazados = []

                for fila in ventas_rechazadas.to_dict("records"):
                    datos = {
                        clave: (
                            None if pd.isna(valor) else str(valor)
                        )
                        for clave, valor in fila.items()
                    }

                    registros_rechazados.append((
                        generar_clave(fila),
                        fuente,
                        fila["motivo"],
                        json.dumps(datos, ensure_ascii=False),
                    ))

                if registros_rechazados:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO ventas_rechazadas (
                            clave_registro, fuente, motivo, datos_originales
                        )
                        VALUES %s
                        ON CONFLICT (clave_registro) DO NOTHING
                        """,
                        registros_rechazados,
                        page_size=1000,
                    )

        print("Carga finalizada correctamente.")

    finally:
        conexion.close()