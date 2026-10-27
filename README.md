# DataMart S.A.S. — Pipeline ETL de ventas con Apache Airflow

Proyecto de análisis de ventas y devoluciones. Convierte archivos CSV en información consultable en PostgreSQL, registra los datos que no pasan las validaciones y permite responder preguntas comerciales mediante SQL.

## ¿Qué hace el proyecto?

1. **Extrae:** comprueba que existan los dos archivos CSV.
2. **Transforma:** normaliza la información y concilia las fuentes para no sumar dos veces facturas que aparecen en ambos archivos.
3. **Valida:** separa registros válidos y rechazados, indicando los motivos de rechazo.
4. **Carga:** guarda ambos grupos en PostgreSQL.

Apache Airflow coordina las cuatro tareas mediante el DAG `datamart_etl_diario`, programado con `@daily`. PostgreSQL guarda las ventas en `ventas` y los rechazos en `ventas_rechazadas`.

## Resultados verificados (27 de octubre de 2026)

| Indicador | Resultado |
|---|---:|
| Filas del CSV histórico | 1.067.371 |
| Filas del CSV reciente | 541.909 |
| Facturas nuevas aportadas por la segunda fuente en esta ejecución | 0 |
| Registros válidos almacenados | 1.064.621 |
| Registros rechazados | 2.750 |
| Importe neto almacenado | 19.445.926,69 |
| Ejecuciones exitosas mostradas en Airflow | 6 de 6 |
| Repetición de carga sin alterar los resultados | Verificada |

**Importante:** los dos CSV contienen datos solapados. Por eso no se suman sus filas directamente. El importe se expresa en las unidades monetarias del archivo de origen; no se le asigna una moneda que los datos no certifiquen.

Las capturas de Airflow, PostgreSQL, idempotencia y consultas están disponibles en **[Evidencias de ejecución](evidencias/README.md)**.

## Archivos de entrada

- **Histórico 2009–2011:** [Online Retail II](https://www.kaggle.com/datasets/thedevastator/online-retail-transaction-dataset) → `data/raw/ventas_2009_2011.csv`.
- **Reciente 2010–2011:** [Ecommerce Data](https://www.kaggle.com/datasets/carrie1/ecommerce-data) → `data/raw/ventas_2010_2011.csv`.

Los CSV no se publican en GitHub por tamaño y condiciones de distribución. Deben descargarse por separado y conservar los nombres indicados.

## Cómo ejecutarlo

**Requisitos:** Docker Desktop con WSL2, Docker Compose, recursos suficientes para procesar más de un millón de registros y ambos CSV.

1. Copiar el archivo de ejemplo y completar las credenciales:
   ```bash
   cp .env.example .env
   ```
2. Iniciar PostgreSQL y preparar Airflow:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d --build postgres_airflow postgres_warehouse
   docker compose -f docker-compose.yml -f docker-compose.airflow.yml run --rm airflow-init
   ```
3. Iniciar los servicios de Airflow:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler
   ```
4. Configurar en Airflow la **Connection** `datamart_warehouse` con la base de datos analítica: host `postgres_warehouse`, puerto `5432`, base de datos, usuario y contraseña definidos para el warehouse. El código de carga consulta esta Connection cuando se ejecuta dentro de Airflow.
5. Abrir [Airflow](http://localhost:8080), iniciar sesión con usuario `admin` y la contraseña `AIRFLOW_ADMIN_PASSWORD`. Activar y ejecutar `datamart_etl_diario`.

La Variable de Airflow `datamart_etl_habilitado` permite habilitar la ejecución; si no se ha definido, el DAG utiliza `true` como valor predeterminado.

**Nota:** esta es la secuencia de configuración del proyecto; no se ha certificado aquí el tiempo de instalación desde una clonación limpia. Si ya tienes el entorno funcionando, no necesitas reinicializarlo.

## Cómo comprobar la carga

Desde la carpeta del proyecto, con los contenedores activos:

```bash
docker compose -f docker-compose.yml -f docker-compose.airflow.yml exec -T postgres_warehouse sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) FROM ventas; SELECT COUNT(*) FROM ventas_rechazadas;"'
```

La carga se repitió y se comprobaron los mismos conteos e importe antes y después. Para evitar confundir líneas distintas con valores comerciales idénticos, la clave SHA-256 de cada registro se calcula a partir del **nombre del archivo de origen y el número de fila original**.

La variable `DATAMART_REBUILD=1` activa una reconstrucción transaccional especial del warehouse. **No se necesita para las ejecuciones normales y no debe activarse sin respaldo y comprobaciones previas.**

## Preguntas de negocio

El archivo **[sql/03_preguntas_negocio.sql](sql/03_preguntas_negocio.sql)** contiene siete análisis:

1. Evolución mensual de las ventas netas.
2. Segmentación técnica de códigos de producto y devoluciones.
3. Productos con mayores ingresos y tasas de devolución.
4. Facturas por país y evolución del ticket promedio.
5. Comparación entre clientes identificados y anónimos.
6. Códigos de producto con descripciones inconsistentes.
7. Productos a priorizar por importe de devoluciones.

Los datos de origen no incluyen categorías comerciales verificadas: los segmentos por formato de código **no son categorías de producto**.

## Documentación adicional

- [Modelo de datos, flujo y limitaciones](docs/modelo_datos_diagramas.md).
- [Evidencias visuales de la ejecución](evidencias/README.md).

## Alcance y limitaciones

- Se implementó un **almacén de datos con tablas transaccionales planas**, no un esquema estrella.
- La conciliación entre archivos se realiza por **factura**: no compara línea por línea las versiones de una misma factura.
- Los clientes sin identificador se conservan como anónimos.
- Las devoluciones se detectan mediante factura que empieza por `C` o cantidad negativa; conviene revisar los casos de signos atípicos.
- La clave basada en archivo y posición conserva líneas idénticas que antes se confundían como duplicadas. Si se modifica el orden o el contenido de los CSV, debe revisarse la identidad de las filas antes de recargar.
- Los scripts de `sql/init` se ejecutan automáticamente al crear un volumen nuevo de PostgreSQL, no cada vez que se reinician los contenedores.
- Power BI es una ampliación visual pendiente; no se presenta como una entrega ya realizada.

## Seguridad

No publicar `.env`, contraseñas, tokens ni los CSV originales. Usar credenciales de desarrollo únicamente en entornos de prueba.
