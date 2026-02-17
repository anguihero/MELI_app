
# Documentación de la Arquitectura de 3 Capas

## Introducción
Este documento describe la arquitectura de 3 capas implementada en el proyecto, detallando las responsabilidades y componentes principales de cada capa: API, Servicios y Persistencia. La arquitectura está diseñada para garantizar modularidad, escalabilidad y facilidad de mantenimiento.

---

## Capa 1: API
### Descripción
La capa de API actúa como la interfaz de comunicación entre los clientes y la aplicación. Está implementada utilizando FastAPI, lo que permite aprovechar características como validación de datos con Pydantic y documentación automática con Swagger UI.

### Responsabilidades
- Exponer endpoints RESTful para interactuar con la aplicación.
- Validar y procesar las solicitudes entrantes.
- Devolver respuestas adecuadas, incluyendo códigos de estado HTTP.

### Componentes Clave
- **Endpoints**:
    - `POST /matches`: Recibe dos textos, calcula el match y persiste el resultado.
    - `POST /matches/compare-by-ids`: Compara dos registros existentes en la base de datos.
    - `GET /matches/{id}`: Recupera un match por su ID.
    - `POST /items`: Permite agregar o actualizar registros en la tabla `items`.
    - `GET /health`: Verifica la conectividad con servicios clave.
    - `GET /tables/{table_name}/header`: Devuelve los nombres de las columnas de una tabla.
    - `POST /matches/backup-and-reset`: Realiza un respaldo y reinicia la tabla `matches`.

---

## Capa 2: Servicios
### Descripción
La capa de servicios encapsula la lógica de negocio de la aplicación. Aquí se implementan las reglas y algoritmos que procesan los datos recibidos desde la capa de API.

### Responsabilidades
- Implementar el algoritmo de similitud de texto.
- Gestionar la lógica de estados (`POSITIVO` y `NEGATIVO`) para los matches.
- Asegurar que las reglas de negocio se cumplan en cada operación.

### Componentes Clave
- **Servicio de Comparación**:
    - Implementa un algoritmo de similitud (e.g., Levenshtein, Jaccard) para calcular un puntaje entre 0 y 1.
- **Lógica de Estados**:
    - Define las reglas para clasificar matches como `POSITIVO` (≥ 0.85) o `NEGATIVO` (< 0.85).
    - Evita recalcular matches con estado `POSITIVO` ya existente.

---

## Capa 3: Persistencia
### Descripción
La capa de persistencia se encarga de la interacción con la base de datos. Está implementada utilizando SQLAlchemy, lo que permite definir modelos y gestionar la base de datos de manera declarativa.

### Responsabilidades
- Definir y gestionar los modelos de datos.
- Proveer una interfaz para realizar operaciones CRUD.
- Configurar la conexión a la base de datos mediante variables de entorno.

### Componentes Clave
- **Modelos**:
    - `items`: Tabla que almacena los registros de items.
    - `matches`: Tabla que almacena los resultados de las comparaciones.
    - `matches_backup`: Tabla utilizada para respaldos de los resultados.
- **Conexión**:
    - Configurada a través de variables de entorno para mayor flexibilidad y seguridad.
- **Script de Inicialización**:
    - Permite crear todas las tablas a partir de los modelos definidos.

---

## Contenerización
### Descripción
La aplicación está diseñada para ejecutarse en un entorno contenerizado, utilizando Docker y Docker Compose.

### Responsabilidades
- Proveer un entorno reproducible para la aplicación y la base de datos.
- Simplificar el despliegue y la configuración.

### Componentes Clave
- **Dockerfile**: Define la imagen de la aplicación.
- **docker-compose.yml**: Orquesta los servicios de la aplicación y la base de datos.

---

## Conclusión
La arquitectura de 3 capas implementada en este proyecto asegura una separación clara de responsabilidades, facilitando el mantenimiento y la escalabilidad de la solución. Cada capa está diseñada para cumplir con su propósito específico, garantizando una interacción eficiente entre ellas.
