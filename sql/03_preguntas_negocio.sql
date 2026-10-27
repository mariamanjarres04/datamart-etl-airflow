-- DataMart: siete preguntas de negocio. Base: public.ventas.
-- Importes en unidades monetarias del origen; devoluciones registradas como negativos.
-- 1. Evolucion mensual de ventas netas
SELECT date_trunc('month',fecha)::date AS mes,
 ROUND(SUM(total) FILTER (WHERE tipo_movimiento='venta'),2) AS ventas_brutas,
 ROUND(COALESCE(SUM(total) FILTER (WHERE tipo_movimiento='devolucion'),0),2) AS devoluciones,
 ROUND(SUM(total),2) AS ventas_netas
FROM ventas GROUP BY 1 ORDER BY 1;
-- 2. Categorias: no existe categoria en fuentes. Segmentos auditables por tipo de codigo;
-- NO son categorias comerciales oficiales.
WITH clasificada AS (
 SELECT CASE WHEN producto ~ '^[0-9]+[A-Z]?$' THEN 'codigo_numerico'
 ELSE 'codigo_especial' END AS segmento, tipo_movimiento,total
 FROM ventas)
SELECT segmento, ROUND(SUM(total) FILTER (WHERE tipo_movimiento='venta'),2) AS bruto,
 ROUND(ABS(COALESCE(SUM(total) FILTER (WHERE tipo_movimiento='devolucion'),0)),2) AS importe_devoluciones,
 ROUND(100*ABS(COALESCE(SUM(total) FILTER (WHERE tipo_movimiento='devolucion'),0))/
 NULLIF(SUM(total) FILTER (WHERE tipo_movimiento='venta'),0),2) AS porcentaje_devolucion_valor
FROM clasificada GROUP BY 1 ORDER BY bruto DESC;
-- 3A. Top diez productos por ingreso neto
SELECT producto, MAX(descripcion) AS descripcion_referencia,
 ROUND(SUM(total),2) AS ingreso_neto
FROM ventas GROUP BY producto ORDER BY ingreso_neto DESC LIMIT 10;
-- 3B. Top diez por tasa de devolucion en unidades, con minimo 100 unidades vendidas
SELECT producto,
 SUM(cantidad) FILTER (WHERE tipo_movimiento='venta') AS unidades_vendidas,
 ABS(COALESCE(SUM(cantidad) FILTER (WHERE tipo_movimiento='devolucion'),0)) AS unidades_devueltas,
 ROUND(100*ABS(COALESCE(SUM(cantidad) FILTER (WHERE tipo_movimiento='devolucion'),0))/
 NULLIF(SUM(cantidad) FILTER (WHERE tipo_movimiento='venta'),0),2) AS tasa_devolucion
FROM ventas GROUP BY producto
HAVING COALESCE(SUM(cantidad) FILTER (WHERE tipo_movimiento='venta'),0)>=100
ORDER BY tasa_devolucion DESC NULLS LAST LIMIT 10;
-- 4. Paises por numero de facturas y evolucion mensual del ticket promedio.
-- El ticket usa importes netos agrupados por factura y pais.
WITH facturas AS (
 SELECT pais,factura,date_trunc('month',MIN(fecha))::date AS mes,SUM(total) AS ticket
 FROM ventas GROUP BY pais,factura
), mensual AS (
 SELECT pais,mes,COUNT(*) AS facturas,ROUND(AVG(ticket),2) AS ticket_promedio
 FROM facturas GROUP BY pais,mes
)
SELECT pais,mes,facturas,ticket_promedio,
 ROUND(ticket_promedio-LAG(ticket_promedio) OVER(PARTITION BY pais ORDER BY mes),2) AS variacion_ticket
FROM mensual ORDER BY SUM(facturas) OVER(PARTITION BY pais) DESC,pais,mes;
-- 5. Identificados vs anonimos
SELECT CASE WHEN cliente IS NULL OR BTRIM(cliente)='' THEN 'anonimo' ELSE 'identificado' END AS segmento,
 COUNT(*) AS lineas,COUNT(DISTINCT factura) AS facturas,ROUND(SUM(total),2) AS ingreso_neto
FROM ventas GROUP BY 1 ORDER BY 1;
-- 6A. Productos con multiples descripciones
SELECT producto,COUNT(DISTINCT LOWER(BTRIM(descripcion))) AS descripciones_distintas,
 ARRAY_AGG(DISTINCT LEFT(descripcion,100)) AS ejemplos
FROM ventas WHERE descripcion IS NOT NULL AND BTRIM(descripcion)<>''
GROUP BY producto HAVING COUNT(DISTINCT LOWER(BTRIM(descripcion)))>1
ORDER BY descripciones_distintas DESC,producto LIMIT 30;
-- 6B. Total de codigos unicos
SELECT COUNT(DISTINCT producto) AS codigos_unicos FROM ventas;
-- 7. Priorizacion de producto por importe absoluto de devoluciones
SELECT producto,MAX(descripcion) AS descripcion_referencia,
 ROUND(SUM(total) FILTER(WHERE tipo_movimiento='venta'),2) AS ventas_brutas,
 ROUND(ABS(COALESCE(SUM(total) FILTER(WHERE tipo_movimiento='devolucion'),0)),2) AS devoluciones_valor,
 ROUND(SUM(total),2) AS ingreso_neto
FROM ventas GROUP BY producto
HAVING COALESCE(SUM(total) FILTER(WHERE tipo_movimiento='venta'),0)>0
ORDER BY devoluciones_valor DESC LIMIT 10;
-- Recomendacion: revisar primero los productos de esta ultima consulta,
-- validando motivos de devolucion y calidad de descripciones antes de intervenir.
