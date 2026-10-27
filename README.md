# DataMart S.A.S. — ETL con Apache Airflow y PostgreSQL

## Objetivo
Pipeline de ventas y devoluciones para analisis comercial. DAG `datamart_etl_diario`: extraccion → transformacion → validacion → carga. PostgreSQL almacena ventas depuradas y rechazos.

## Requisitos
Docker Desktop con WSL2, Docker Compose, al menos 6 GB RAM disponibles y los CSV originales de Kaggle.

## Fuentes
1. [Online Retail II (2009–2011)](https://www.kaggle.com/datasets/thedevastator/online-retail-transaction-dataset): guardar CSV historico en `data/raw/ventas_2009_2011.csv`.
2. [Ecommerce Data (2010–2011)](https://www.kaggle.com/datasets/carrie1/ecommerce-data): guardar `data.csv` como `data/raw/ventas_2010_2011.csv`.

**Limitacion importante:** el DAG actual carga el archivo historico y no integra aun la segunda fuente; existe solapamiento de facturas entre ambos datasets. No deben sumarse sin conciliacion.

## Arranque
```bash
cp .env.example .env
# Completar contrasenas y secreto en .env
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d --build postgres_airflow postgres_warehouse
docker compose -f docker-compose.yml -f docker-compose.airflow.yml run --rm airflow-init
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler
```
Abrir http://localhost:8080, ingresar con usuario `admin` y contraseña configurada como `AIRFLOW_ADMIN_PASSWORD`. Activar DAG `datamart_etl_diario` y ejecutar manualmente. Requiere descargar previamente el CSV historico; los CSV no se incluyen en Git por su tamaño y licencia.

## Validacion
```bash
docker compose exec -T postgres_warehouse sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) FROM ventas; SELECT COUNT(*) FROM ventas_rechazadas;"'
```
Ejecucion verificada en entorno de desarrollo: 1.030.410 filas en `ventas` y 2.626 claves unicas en `ventas_rechazadas`. La validacion original proceso 1.064.621 filas validas y 2.750 rechazadas; los conteos de tablas reflejan deduplicacion por hash.

## Modelo de datos
```text
CSV historico --> Airflow [extraccion -> transformacion -> validacion -> carga]
                                                        |
                                             PostgreSQL warehouse
                                             |                 |
                                           ventas      ventas_rechazadas
```
**Modelo actual:** tabla transaccional plana `ventas`, no esquema estrella. Una fila representa una combinacion de atributos comerciales unica segun hash; **no necesariamente cada linea original de factura**. Campos: factura, producto, descripcion, cantidad, fecha, precio, cliente, pais, tipo_movimiento, total, fuente y clave_registro.

## Consultas de negocio
Archivo `sql/03_preguntas_negocio.sql`: evolucion mensual neta, segmentos por codigo, productos top y devoluciones, paises/ticket, clientes anonimos, descripciones inconsistentes y recomendacion priorizada.

## Decisiones y limites de calidad
- Las devoluciones se identifican por factura que inicia en C o cantidad negativa. Importe `cantidad * precio`; hay que revisar casos de signos atipicos.
- Los clientes sin ID se consideran anonimos; no se inventan identidades.
- El dataset no ofrece categorias comerciales fiables. La consulta 2 usa **segmentos tecnicos por formato de codigo**, que NO equivalen a categorias reales.
- El hash actual elimina 34.211 filas validas identicas en atributos, asociadas a 431.716,87 unidades monetarias netas. No se puede demostrar que sean duplicados comerciales: esto puede sesgar indicadores. Requiere redisenar identificador de fila por version de fuente + numero de linea y reconciliar los dos CSV.
- La carga usa `ON CONFLICT DO NOTHING` para evitar duplicados en reejecuciones, sujeto a la limitacion anterior.
- SQL de `sql/init` se aplica automaticamente solo al crear un volumen nuevo de PostgreSQL.
- Variables y Connections de Airflow: la version actual usa variables de entorno `WAREHOUSE_DB_*` inyectadas por Docker Compose, no Connections/Variables administradas desde Airflow. Pendiente para cumplimiento completo.
- El arranque incluye pasos de inicializacion y requiere archivos descargados; no se ha verificado una instalacion limpia en menos de diez minutos.

## Seguridad
No subir `.env` ni los CSV. Usar credenciales de desarrollo y rotarlas antes de despliegue.

## Estado
Pipeline probado exitosamente en Docker Airflow; las limitaciones anteriores se documentan expresamente y no se presentan como funcionalidades implementadas.
