import pandas as pd  # Permite trabajar con tablas de datos.


def validar_ventas(ventas):
    # Creamos una copia para no modificar la tabla recibida.
    datos = ventas.copy()

    # Revisamos si faltan datos necesarios para identificar una venta.
    sin_factura = datos["factura"].isna() | (datos["factura"] == "")
    sin_producto = datos["producto"].isna() | (datos["producto"] == "")
    sin_fecha = datos["fecha"].isna()

    # Revisamos cantidades y precios que no pueden procesarse.
    cantidad_invalida = datos["cantidad"].isna() | (datos["cantidad"] == 0)
    precio_invalido = datos["precio"].isna() | (datos["precio"] < 0)

    # Una venta positiva debe tener un precio mayor que cero.
    # Las devoluciones se analizarán por separado.
    venta_sin_precio = (
        (datos["tipo_movimiento"] == "venta")
        & (datos["precio"] == 0)
    )

    # Marcamos las filas que incumplen alguna validación.
    rechazado = (
        sin_factura
        | sin_producto
        | sin_fecha
        | cantidad_invalida
        | precio_invalido
        | venta_sin_precio
    )

    # Separamos los registros para conservar también los rechazados.
    ventas_validas = datos.loc[~rechazado].copy()
    ventas_rechazadas = datos.loc[rechazado].copy()

    # Guardamos una explicación sencilla de cada rechazo.
    ventas_rechazadas["motivo"] = "Registro con datos obligatorios inválidos"

    return ventas_validas, ventas_rechazadas