# DAG: automatiza las etapas del ETL de DataMart.
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator


# Carpeta donde estarán los archivos dentro de Airflow.
RAIZ = Path("/opt/airflow")
DATOS = RAIZ / "data"
FUENTE = DATOS / "raw" / "ventas_2009_2011.csv"


def ejecutar_codigo(codigo):
    """Ejecuta una etapa usando Python dentro del contenedor."""
    subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=str(RAIZ),
        check=True,
    )


def extraer():
    # Verificamos que exista el archivo de entrada.
    if not FUENTE.is_file():
        raise FileNotFoundError(f"No existe el CSV: {FUENTE}")

    print("Extracción: archivo disponible.")


def transformar():
    # Aplicamos las transformaciones existentes y guardamos el resultado.
    ejecutar_codigo("""
import pandas as pd
from etl.transformacion_ventas import transformar_ventas

ventas = pd.read_csv(
    "data/raw/ventas_2009_2011.csv",
    encoding="latin-1",
    low_memory=False
)
datos = transformar_ventas(ventas)
datos.to_pickle("data/processed/ventas_transformadas.pkl")
print("Transformación completada:", len(datos))
""")


def validar():
    # Separamos los registros válidos de los rechazados.
    ejecutar_codigo("""
import pandas as pd
from etl.validacion_ventas import validar_ventas

datos = pd.read_pickle("data/processed/ventas_transformadas.pkl")
validas, rechazadas = validar_ventas(datos)

validas.to_pickle("data/processed/ventas_validas.pkl")
rechazadas.to_pickle("data/rejected/ventas_rechazadas.pkl")

print("Válidos:", len(validas))
print("Rechazados:", len(rechazadas))
""")


def cargar():
    # Insertamos los resultados en PostgreSQL.
    ejecutar_codigo("""
import pandas as pd
from etl.carga_ventas import cargar_ventas

validas = pd.read_pickle("data/processed/ventas_validas.pkl")
rechazadas = pd.read_pickle("data/rejected/ventas_rechazadas.pkl")

cargar_ventas(
    validas,
    rechazadas,
    fuente="ventas_2009_2011.csv"
)
print("Carga completada.")
""")


with DAG(
    dag_id="datamart_etl_diario",
    description="Pipeline ETL diario de ventas y devoluciones",
    start_date=datetime(2026, 10, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={
        "owner": "datamart",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["etl", "ventas", "warehouse"],
) as dag:

    tarea_extraccion = PythonOperator(
        task_id="extraccion",
        python_callable=extraer,
    )

    tarea_transformacion = PythonOperator(
        task_id="transformacion",
        python_callable=transformar,
    )

    tarea_validacion = PythonOperator(
        task_id="validacion",
        python_callable=validar,
    )

    tarea_carga = PythonOperator(
        task_id="carga",
        python_callable=cargar,
    )

    # Establecemos el orden obligatorio del pipeline.
    tarea_extraccion >> tarea_transformacion >> tarea_validacion >> tarea_carga