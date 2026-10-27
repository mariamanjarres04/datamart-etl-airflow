-- 1. Resumen de ventas y devoluciones
SELECT tipo_movimiento, COUNT(*) AS registros, SUM(total) AS valor
FROM ventas
GROUP BY tipo_movimiento;

-- 2. Los 10 países con mayores ventas
SELECT pais, ROUND(SUM(total), 2) AS ingresos
FROM ventas
WHERE tipo_movimiento = 'venta'
GROUP BY pais
ORDER BY ingresos DESC
LIMIT 10;

-- 3. Los 10 productos más vendidos por valor
SELECT producto, MAX(descripcion) AS descripcion,
       SUM(cantidad) AS unidades, ROUND(SUM(total), 2) AS ingresos
FROM ventas
WHERE tipo_movimiento = 'venta'
GROUP BY producto
ORDER BY ingresos DESC
LIMIT 10;

-- 4. Ventas mensuales
SELECT DATE_TRUNC('month', fecha)::date AS mes,
       ROUND(SUM(total), 2) AS ingresos
FROM ventas
WHERE tipo_movimiento = 'venta'
GROUP BY mes
ORDER BY mes;

-- 5. Los 10 clientes con mayores compras
SELECT cliente, COUNT(DISTINCT factura) AS facturas,
       ROUND(SUM(total), 2) AS total_comprado
FROM ventas
WHERE tipo_movimiento = 'venta' AND cliente IS NOT NULL
GROUP BY cliente
ORDER BY total_comprado DESC
LIMIT 10;

-- 6. Impacto de las devoluciones
SELECT COUNT(*) AS devoluciones,
       ROUND(SUM(ABS(total)), 2) AS valor_devuelto
FROM ventas
WHERE tipo_movimiento = 'devolucion';

-- 7. Auditoría de calidad
SELECT
    (SELECT COUNT(*) FROM ventas) AS registros_validos,
    (SELECT COUNT(*) FROM ventas_rechazadas) AS registros_rechazados;
