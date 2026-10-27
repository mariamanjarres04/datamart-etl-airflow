import pandas as pd  # Nos permite trabajar con tablas de datos.


def transformar_ventas(ventas):
    # Creamos una copia para conservar los datos originales.
    datos = ventas.copy()

    # Igualamos los nombres de las columnas.
    datos = datos.rename(columns={
        "Invoice": "factura",
        "InvoiceNo": "factura",
        "StockCode": "producto",
        "Description": "descripcion",
        "Quantity": "cantidad",
        "InvoiceDate": "fecha",
        "Price": "precio",
        "UnitPrice": "precio",
        "Customer ID": "cliente",
        "CustomerID": "cliente",
        "Country": "pais"
    })

    # Quitamos espacios sobrantes de los códigos y las facturas.
    datos["factura"] = datos["factura"].astype("string").str.strip()
    datos["producto"] = datos["producto"].astype("string").str.strip().str.upper()

    # Convertimos cantidades y precios a números.
    # Si un valor no se puede convertir, quedará vacío para revisarlo.
    datos["cantidad"] = pd.to_numeric(
        datos["cantidad"], errors="coerce"
    )
    datos["precio"] = pd.to_numeric(
        datos["precio"], errors="coerce"
    )

    # Convertimos las fechas para poder analizarlas por día o mes.
    datos["fecha"] = pd.to_datetime(
        datos["fecha"], errors="coerce", utc=True
    )

    # Identificamos devoluciones mediante facturas canceladas
    # o cantidades negativas.
    es_devolucion = (
        datos["factura"].str.upper().str.startswith("C", na=False)
        | (datos["cantidad"] < 0)
    )

    # Clasificamos cada movimiento comercial.
    datos["tipo_movimiento"] = "venta"
    datos.loc[es_devolucion, "tipo_movimiento"] = "devolucion"

    # Calculamos el valor de cada línea de factura.
    # Las cantidades negativas producen importes negativos.
    datos["total"] = datos["cantidad"] * datos["precio"]

    return datos