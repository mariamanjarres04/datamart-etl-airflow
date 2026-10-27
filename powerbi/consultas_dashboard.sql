-- Vistas para Power BI. No modifican las ventas originales.
-- Ejecutar en la base datamart. Los importes conservan la unidad monetaria del CSV.
CREATE OR REPLACE VIEW public.bi_resumen AS
SELECT COUNT(*)::bigint AS lineas_validas,
       COUNT(DISTINCT factura)::bigint AS facturas,
       ROUND(COALESCE(SUM(total),0),2) AS ventas_netas,
       ROUND(COALESCE(SUM(total) FILTER (WHERE tipo_movimiento='venta'),0),2) AS ventas_brutas,
       ROUND(ABS(COALESCE(SUM(total) FILTER (WHERE tipo_movimiento='devolucion'),0)),2) AS devoluciones
FROM public.ventas;

CREATE OR REPLACE VIEW public.bi_ventas_mensuales AS
SELECT date_trunc('month',fecha)::date AS mes,
       ROUND(COALESCE(SUM(total),0),2) AS ventas_netas,
       ROUND(COALESCE(SUM(total) FILTER (WHERE tipo_movimiento='venta'),0),2) AS ventas_brutas,
       ROUND(ABS(COALESCE(SUM(total) FILTER (WHERE tipo_movimiento='devolucion'),0)),2) AS devoluciones
FROM public.ventas GROUP BY 1;

CREATE OR REPLACE VIEW public.bi_paises AS
SELECT pais,
       COUNT(DISTINCT factura)::bigint AS facturas,
       ROUND(COALESCE(SUM(total),0),2) AS ventas_netas
FROM public.ventas GROUP BY pais;

CREATE OR REPLACE VIEW public.bi_productos AS
SELECT producto, MAX(descripcion) AS descripcion_referencia,
       ROUND(COALESCE(SUM(total),0),2) AS ingreso_neto,
       ROUND(ABS(COALESCE(SUM(total) FILTER (WHERE tipo_movimiento='devolucion'),0)),2) AS devoluciones
FROM public.ventas GROUP BY producto;

CREATE OR REPLACE VIEW public.bi_clientes AS
SELECT CASE WHEN cliente IS NULL OR BTRIM(cliente)='' THEN 'Anónimo' ELSE 'Identificado' END AS segmento,
       COUNT(*)::bigint AS lineas,
       COUNT(DISTINCT factura)::bigint AS facturas,
       ROUND(COALESCE(SUM(total),0),2) AS ingreso_neto
FROM public.ventas GROUP BY 1;

CREATE OR REPLACE VIEW public.bi_calidad AS
SELECT COUNT(*)::bigint AS registros_rechazados FROM public.ventas_rechazadas;
