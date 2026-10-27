# Power BI — Dashboard de DataMart S.A.S.

## Objetivo

Mostrar los resultados reales del ETL en un tablero ejecutivo fácil de leer: ventas netas, evolución mensual, países, productos, clientes y calidad de datos.

**Estado:** preparación técnica lista; el archivo `.pbix` todavía debe construirse y guardarse desde Power BI Desktop. No se afirma que exista un dashboard terminado.

## 1. Preparar PostgreSQL

Con los contenedores activos, ejecutar el archivo [consultas_dashboard.sql](consultas_dashboard.sql) contra la base `datamart`. Crea seis **vistas** de solo lectura para Power BI; no borra ni altera las transacciones originales.

Desde la raíz del repositorio en WSL:

```bash
docker compose -f docker-compose.yml -f docker-compose.airflow.yml exec -T postgres_warehouse sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < powerbi/consultas_dashboard.sql
```

Para comprobar el resultado:

```bash
docker compose -f docker-compose.yml -f docker-compose.airflow.yml exec -T postgres_warehouse sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT * FROM public.bi_resumen;"'
```

**Nota:** el comando anterior crea vistas en la base que ya funciona. No ejecutar `docker compose down -v`, pues eliminaría los volúmenes con datos.

## 2. Conectar Power BI Desktop

En Windows, abrir Power BI Desktop → **Obtener datos → Base de datos PostgreSQL**.

- Servidor: `localhost:5544` (puerto publicado por Docker en Windows).
- Base de datos: el valor de `WAREHOUSE_DB_NAME` de `.env` (en la configuración de ejemplo, `datamart`).
- Credenciales: `WAREHOUSE_DB_USER` y `WAREHOUSE_DB_PASSWORD` del archivo local `.env`.
- Modo: **Importar**.
- Elegir las vistas `public.bi_resumen`, `public.bi_ventas_mensuales`, `public.bi_paises`, `public.bi_productos`, `public.bi_clientes` y `public.bi_calidad`.

Si Power BI solicita instalar el controlador de PostgreSQL (Npgsql), seguir las indicaciones oficiales de Power BI. No compartir contraseñas ni publicar `.env`.

## 3. Diseñar el dashboard

Propuesta de una página **Resumen ejecutivo**:

1. Tarjeta **Ventas netas** → `bi_resumen[ventas_netas]`.
2. Tarjeta **Facturas** → `bi_resumen[facturas]`.
3. Tarjeta **Registros rechazados** → `bi_calidad[registros_rechazados]`.
4. Gráfico de líneas **Evolución mensual** → eje `bi_ventas_mensuales[mes]`, valor `ventas_netas`.
5. Gráfico de barras **Países con mayores ventas** → eje `bi_paises[pais]`, valor `ventas_netas`, orden descendente.
6. Gráfico de barras **Productos por ingreso neto** → eje `bi_productos[producto]`, valor `ingreso_neto`, filtro Top N = 10.
7. Gráfico de columnas **Clientes identificados y anónimos** → eje `bi_clientes[segmento]`, valor `ingreso_neto`.

Usar un diseño sobrio, fondo claro, tipografía legible y títulos comprensibles. Los valores monetarios **no deben mostrar símbolo de moneda** si el origen no certifica la divisa.

## 4. Validación

Comprobar que `bi_resumen[ventas_netas]` coincida con **19.445.926,69** y `bi_calidad[registros_rechazados]` con **2.750** en el entorno ya verificado. Si no coinciden, revisar la conexión, las vistas y si el ETL se volvió a ejecutar.

Las vistas muestran datos **actualizados al último refresco de Power BI**. No implican actualización en tiempo real.

## 5. Entrega

Guardar el archivo desde Power BI Desktop como `powerbi/DataMart_Dashboard.pbix`. Solo después de crear y verificar el archivo se puede considerar terminada la parte de Power BI. El archivo `.pbix` no está incluido todavía en el repositorio.
