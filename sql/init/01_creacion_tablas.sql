-- Tabla principal: almacena las ventas y devoluciones válidas.
CREATE TABLE IF NOT EXISTS ventas (
    id BIGSERIAL PRIMARY KEY,

    -- Identificador único para evitar cargar dos veces el mismo registro.
    clave_registro VARCHAR(64) NOT NULL UNIQUE,

    factura VARCHAR(50) NOT NULL,
    producto VARCHAR(50) NOT NULL,
    descripcion TEXT,
    cantidad NUMERIC(12, 2) NOT NULL,
    fecha TIMESTAMPTZ NOT NULL,
    precio NUMERIC(14, 2) NOT NULL,
    cliente VARCHAR(50),
    pais VARCHAR(100),
    tipo_movimiento VARCHAR(20) NOT NULL,
    total NUMERIC(16, 2) NOT NULL,

    -- Identifica el archivo de donde provienen los datos.
    fuente VARCHAR(100) NOT NULL,

    fecha_carga TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de auditoría: conserva los registros rechazados.
CREATE TABLE IF NOT EXISTS ventas_rechazadas (
    id BIGSERIAL PRIMARY KEY,

    -- Permite evitar rechazos duplicados en nuevas ejecuciones.
    clave_registro VARCHAR(64) NOT NULL UNIQUE,

    fuente VARCHAR(100) NOT NULL,
    motivo TEXT NOT NULL,
    datos_originales JSONB NOT NULL,

    fecha_rechazo TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Índices para agilizar consultas del negocio.
CREATE INDEX IF NOT EXISTS idx_ventas_fecha
ON ventas (fecha);

CREATE INDEX IF NOT EXISTS idx_ventas_producto
ON ventas (producto);

CREATE INDEX IF NOT EXISTS idx_ventas_pais
ON ventas (pais);

CREATE INDEX IF NOT EXISTS idx_ventas_tipo
ON ventas (tipo_movimiento);