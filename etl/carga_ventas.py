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
    """Identifica una línea física del CSV, incluso si coincide en valores con otra."""
    origen = fila.get("fuente_origen")
    posicion = fila.get("numero_fila_origen")
    if pd.notna(origen) and pd.notna(posicion):
        return hashlib.sha256(f"{origen}|{int(posicion)}".encode("utf-8")).hexdigest()
    raise ValueError("Falta fuente_origen o numero_fila_origen: no es seguro cargar con clave por contenido")


def clave_anterior_no_utilizar(fila):
    """Clave histórica conservada solo como referencia de auditoría."""

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

    # Airflow administra las credenciales mediante una Connection.
    # En ejecuciones locales se conservan las variables del archivo .env.
    if os.getenv("AIRFLOW_HOME"):
        from airflow.hooks.base import BaseHook

        configuracion = BaseHook.get_connection("datamart_warehouse")
        conexion = psycopg2.connect(
            host=configuracion.host,
            port=configuracion.port,
            dbname=configuracion.schema,
            user=configuracion.login,
            password=configuracion.password,
        )
    else:
        conexion = psycopg2.connect(
            host=os.getenv("WAREHOUSE_DB_HOST", "localhost"),
            port=os.getenv("WAREHOUSE_DB_PORT", "5544"),
            dbname=os.getenv("WAREHOUSE_DB_NAME"),
            user=os.getenv("WAREHOUSE_DB_USER"),
            password=os.getenv("WAREHOUSE_DB_PASSWORD"),
        )

    reconstruir = os.getenv("DATAMART_REBUILD", "0") == "1"
    if reconstruir:
        if ventas_validas.empty or "numero_fila_origen" not in ventas_validas.columns:
            conexion.close()
            raise ValueError("Reconstrucción bloqueada: faltan filas o identificadores de origen")
        if ventas_validas[["fuente_origen", "numero_fila_origen"]].isna().any().any():
            conexion.close()
            raise ValueError("Reconstrucción bloqueada: identificadores de origen nulos")

    try:
        with conexion:
            with conexion.cursor() as cursor:

                # La reconstrucción utiliza tablas temporales y una sola transacción.
                # Un fallo antes del COMMIT revierte el reemplazo completo.
                if reconstruir:
                    cursor.execute("CREATE TEMP TABLE ventas_stage (LIKE public.ventas INCLUDING ALL) ON COMMIT DROP")
                    cursor.execute("CREATE TEMP TABLE rechazos_stage (LIKE public.ventas_rechazadas INCLUDING ALL) ON COMMIT DROP")
                destino_ventas = "ventas_stage" if reconstruir else "ventas"
                destino_rechazos = "rechazos_stage" if reconstruir else "ventas_rechazadas"

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
                        INSERT INTO {destino_ventas} (
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
                        INSERT INTO {destino_rechazos} (
                            clave_registro, fuente, motivo, datos_originales
                        )
                        VALUES %s
                        ON CONFLICT (clave_registro) DO NOTHING
                        """,
                        registros_rechazados,
                        page_size=1000,
                    )

                if reconstruir:
                    cursor.execute("SELECT COUNT(*) FROM ventas_stage")
                    validas_stage = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM rechazos_stage")
                    rechazos_stage = cursor.fetchone()[0]
                    if validas_stage != len(ventas_validas) or rechazos_stage != len(ventas_rechazadas):
                        raise RuntimeError(f"Recuento inesperado: {validas_stage}/{len(ventas_validas)} ventas, {rechazos_stage}/{len(ventas_rechazadas)} rechazos")
                    # El reemplazo y sus verificaciones se confirman de forma atómica.
                    cursor.execute("TRUNCATE TABLE public.ventas, public.ventas_rechazadas")
                    cursor.execute("""INSERT INTO public.ventas (clave_registro, factura, producto, descripcion, cantidad, fecha, precio, cliente, pais, tipo_movimiento, total, fuente)
                        SELECT clave_registro, factura, producto, descripcion, cantidad, fecha, precio, cliente, pais, tipo_movimiento, total, fuente FROM ventas_stage""")
                    cursor.execute("""INSERT INTO public.ventas_rechazadas (clave_registro, fuente, motivo, datos_originales)
                        SELECT clave_registro, fuente, motivo, datos_originales FROM rechazos_stage""")
                    cursor.execute("SELECT COUNT(*) FROM public.ventas")
                    if cursor.fetchone()[0] != validas_stage:
                        raise RuntimeError("Recuento posterior a reconstrucción no coincide")
                    print(f"Reconstrucción transaccional: {validas_stage} ventas y {rechazos_stage} rechazos")

        print("Carga finalizada correctamente.")

    finally:
        conexion.close()