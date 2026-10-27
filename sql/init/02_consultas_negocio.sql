-- 1. Total de movimientos almacenados.
SELECT
    tipo_movimiento,
    COUNT(*) AS cantidad_movimientos,
    ROUND(SUM(total), 2) AS valor_total
FROM ventas
GROUP BY tipo_movimiento;


-- 2. Ventas por país, excluyendo devoluciones.
SELECT
    pais,
    COUNT(*) AS cantidad_registros,
    ROUND(SUM(total), 2) AS ingresos
FROM ventas
WHERE tipo_movimiento = 'venta'
GROUP BY pais
ORDER BY ingresos DESC
LIMIT 10;


-- 3. Productos con mayor valor vendido.
SELECT
    producto,
    MAX(descripcion) AS descripcion,
    SUM(cantidad) AS unidades_vendidas,
    ROUND(SUM(total), 2) AS ingresos
FROM ventas
WHERE tipo_movimiento = 'venta'
GROUP BY producto
ORDER BY ingresos DESC
LIMIT 10;


-- 4. Evolución mensual de ventas.
SELECT
    DATE_TRUNC('month', fecha)::date AS mes,
    COUNT(*) AS registros,
    ROUND(SUM(total), 2) AS ingresos
FROM ventas
WHERE tipo_movimiento = 'venta'
GROUP BY mes
ORDER BY mes;


-- 5. Clientes con mayor valor de compras.
SELECT
    cliente,
    COUNT(DISTINCT factura) AS facturas,
    ROUND(SUM(total), 2) AS total_comprado
FROM ventas
WHERE tipo_movimiento = 'venta'
  AND cliente IS NOT NULL
GROUP BY cliente
ORDER BY total_comprado DESC
LIMIT 10;


-- 6. Impacto de las devoluciones.
SELECT
    COUNT(*) AS cantidad_devoluciones,
    ROUND(SUM(ABS(total)), 2) AS valor_devuelto
FROM ventas
WHERE tipo_movimiento = 'devolucion';


-- 7. Calidad de los datos procesados.
SELECT
    (SELECT COUNT(*) FROM ventas) AS registros_validos_almacenados,
    (SELECT COUNT(*) FROM ventas_rechazadas) AS registros_rechazados_almacenados;