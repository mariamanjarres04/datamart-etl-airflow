# Importamos las herramientas necesarias para ejecutar nuestro ETL.
from pathlib import Path
import sys

import pandas as pd

# Localizamos la raíz del proyecto, sin depender de la carpeta
# desde la que se ejecute Python.
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from etl.transformacion_ventas import transformar_ventas
from etl.validacion_ventas import validar_ventas
from etl.carga_ventas import cargar_ventas


def ejecutar_etl():
    # EXTRACT: leemos el CSV histórico que seleccionamos como fuente.
    ruta_csv = RAIZ / "data" / "raw" / "ventas_2009_2011.csv"

    print("1. Leyendo el archivo CSV...")
    ventas = pd.read_csv(ruta_csv, encoding="latin-1", low_memory=False)
    print("Registros extraídos:", len(ventas))

    # TRANSFORM: unificamos nombres y tipos de datos.
    print("2. Transformando los datos...")
    ventas_transformadas = transformar_ventas(ventas)

    # VALIDATE: separamos los registros válidos de los rechazados.
    print("3. Validando los registros...")
    ventas_validas, ventas_rechazadas = validar_ventas(
        ventas_transformadas
    )

    print("Registros válidos:", len(ventas_validas))
    print("Registros rechazados:", len(ventas_rechazadas))

    # LOAD: guardamos los resultados en PostgreSQL.
    print("4. Cargando el Data Warehouse...")
    cargar_ventas(
        ventas_validas,
        ventas_rechazadas,
        fuente="ventas_2009_2011.csv",
    )

    print("ETL FINALIZADO")


if __name__ == "__main__":
    ejecutar_etl()