# MELI CHALLENGE API - DOCUMENTACIÓN COMPLETA DEL MÓDULO MAIN.PY

## Descripción General

Módulo principal de la API FastAPI para el Desafío de Desarrollo Op 2 - AA&ML de MercadoLibre. Proporciona endpoints RESTful para gestión de items, comparación de similitudes entre textos y productos, y operaciones sobre matches.

- **Autor:** Andrés Muñoz
- **Versión:** 1.0.0
- **Fecha:** 2026/2/17

---

## Sección 1: Importaciones y Dependencias

### FastAPI Core
- **FastAPI:** Framework web para construir APIs REST asincrónicas
- **HTTPException:** Clase para lanzar excepciones HTTP con códigos de estado
- **status:** Módulo con constantes de códigos de estado HTTP (201, 404, 500, etc)
- **Path:** Parámetro de ruta que permite validar y documentar rutas dinámicas
- **Depends:** Sistema de inyección de dependencias para reutilizar lógica

### Pydantic Models
- **BaseModel:** Clase base para definir schemas de validación de datos con tipos
- **Field:** Función para documentar campos de modelos con descripciones y ejemplos
- **Enum:** Clase para definir enumeraciones de valores discretos y válidos

### Type Hints
- **List:** Para anotaciones de tipo de listas genéricas
- **Dict:** Para anotaciones de tipo de diccionarios genéricos
- **Any:** Para anotaciones de tipo sin restricciones específicas

### SQLAlchemy Database
- **create_engine:** Constructor de motores de conexión a bases de datos
- **text:** Constructor para consultas SQL con escaping automático
- **inspect:** Herramienta para introspección de metadatos de BD (tablas, columnas)
- **Session:** Contexto de sesión para operaciones transaccionales en la BD

### Excepciones Database
- **NoSuchTableError:** Excepción lanzada cuando se intenta acceder a tabla inexistente
    > **Nota:** Se importa pero no se utiliza directamente; considerar remover o usar en validaciones

### Utilities
- **os:** Módulo para acceder a variables de entorno del sistema operativo

---

## Sección 2: Enumeraciones (Enums)

### StatusEnum

```python
class StatusEnum(str, Enum)
```

Enumeración que define los estados válidos de un match en el sistema.

**Herencia doble:**
- `str`: Representa el enum como string serializable en JSON
- `Enum`: Proporciona funcionalidad estándar de enumeración Python

**Valores válidos:**
- `"positivo"`: Match confirmado como positivo/similar
- `"en progreso"`: Match bajo evaluación/pendiente de confirmación
- `"negativo"`: Match confirmado como negativo/no similar

**Propósito:** Garantiza consistencia de datos y previene valores inválidos en BD

---

## Sección 3: Modelos Pydantic (Schemas de Validación)

### ItemCreate

```python
class ItemCreate(BaseModel)
```

Schema para validar datos de entrada al crear un nuevo item/producto.

**Atributos:**
- `id` (str): Identificador único del producto en MercadoLibre (ej: MLA123456)
- `title` (str): Título o nombre descriptivo del producto

**Propósito:** Validar estructura de datos antes de procesar en endpoints POST

### ItemResponse

```python
class ItemResponse(ItemCreate)
```

Schema para respuesta al crear/actualizar un item exitosamente.

**Hereda de:** ItemCreate

**Atributos adicionales:**
- `message` (str): Confirmación de operación ("Item creado/actualizado correctamente.")

**Propósito:** Respuesta consistente y confirmación de operación al cliente

### MatchCreate

```python
class MatchCreate(BaseModel)
```

Schema para validar datos de entrada al crear match desde dos textos.

**Atributos:**
- `text_1` (str): Primer texto a comparar (puede ser título de producto)
- `text_2` (str): Segundo texto a comparar (puede ser título de producto)

**Propósito:** Entrada para endpoint de comparación de textos sin IDs previos

### MatchCompare

```python
class MatchCompare(BaseModel)
```

Schema para validar datos de entrada al comparar dos items existentes.

**Atributos:**
- `id_a` (str): Identificador del primer producto en BD
- `id_b` (str): Identificador del segundo producto en BD

**Propósito:** Entrada para endpoint que compara productos ya presentes en BD

### MatchResponse

```python
class MatchResponse(BaseModel)
```

Schema para respuesta al retrieval o creación de un match.

**Atributos:**
- `id` (int): Identificador único del match en tabla matches
- `id_item_1` (str): ID del primer producto relacionado
- `title_item_1` (str): Título del primer producto
- `id_item_2` (str): ID del segundo producto relacionado
- `title_item_2` (str): Título del segundo producto
- `score` (float): Puntuación de similitud: rango [0.0, 1.0] (ej: 0.95 = 95%)
- `status` (StatusEnum): Estado actual del match (positivo/en_progreso/negativo)

**Propósito:** Respuesta estándar del sistema para queries sobre matches

### HealthResponse

```python
class HealthResponse(BaseModel)
```

Schema para respuesta del endpoint de health check.

**Atributos:**
- `status` (str): Indica salud del sistema ("ok" = operativo)

**Propósito:** Respuesta simple para validar disponibilidad de API

### TableHeaderResponse

```python
class TableHeaderResponse(BaseModel)
```

Schema para respuesta de consulta de metadata de tablas.

**Atributos:**
- `table_name` (str): Nombre de la tabla consultada en BD
- `columns` (list[str]): Lista de nombres de columnas de la tabla

**Propósito:** Introspección de estructura de BD sin exponerla completamente

### BackupResponse

```python
class BackupResponse(BaseModel)
```

Schema para respuesta de operación de backup y reset de matches.

**Atributos:**
- `message` (str): Descripción de operación realizada
- `records_moved` (int): Cantidad de registros transferidos a backup

**Propósito:** Confirmación y auditoría de operaciones destructivas (datos movidos)

---

## Sección 4: Configuración de Base de Datos

### DATABASE_URL

Variable de entorno con cadena de conexión a PostgreSQL.

**Estructura:** `postgresql://[usuario]:[contraseña]@[host]:[puerto]/[base_datos]`

**Propósito:** Conectar con BD de producción; credenciales gestionadas por Hub central de infraestructura (evitar hardcoding en código)

**Valor por defecto:** BD local en localhost (desarrollo/testing)

**Nota de seguridad:** En producción, NUNCA hardcodear credenciales

### engine

Motor SQLAlchemy que gestiona pool de conexiones con BD.

**Propósito:**
- Pool de conexiones reutilizables (mejora rendimiento)
- Traducción de consultas SQL a dialecto específico (PostgreSQL)
- Introspección de metadatos (tablas, columnas, índices)

**Configuración implícita:**
- pool_size = 5 conexiones por defecto
- max_overflow = 10 conexiones adicionales bajo carga

### get_db()

```python
def get_db()
```

Generador (generator) que proporciona sesión de BD como dependencia inyectable.

**Flujo:**
1. `yield db`: Proporciona sesión abierta al endpoint
2. Endpoint procesa solicitud usando 'db'
3. `finally db.close()`: Cierra sesión automáticamente (cleanup)

**Patrón:** Context Manager pattern en FastAPI (Depends)

**Beneficios:**
- Sesiones cerradas automáticamente (evita memory leaks)
- Reutilizable en cualquier endpoint vía `Depends(get_db)`
- Desacoplamiento entre lógica de negocio y gestión de BD

---

## Sección 5: Instanciación de Aplicación FastAPI

### app

```python
app = FastAPI(...)
```

Crea instancia principal de aplicación FastAPI con configuración.

**Parámetros:**
- `title`: Título de API (visible en documentación Swagger)
- `description`: Descripción larga con contexto del proyecto
- `version`: Versionado semántico (MAJOR.MINOR.PATCH)

**Propósito:**
- Punto de entrada para servidor ASGI (Uvicorn, Gunicorn)
- Genera documentación interactiva (Swagger UI, ReDoc)
- Registra todos los endpoints (decoradores @app.get/@app.post)

**URL de documentación automática:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Sección 6: Endpoints (Rutas HTTP)

### GET /health

```python
async def health_check()
```

**Propósito:** Verificar disponibilidad y conectividad con BD

**Implementación esperada:**
1. Ejecutar consulta trivial en BD (SELECT 1 FROM dual)
2. Si falla → HTTPException(503 Service Unavailable)
3. Si éxito → Retornar HealthResponse(status="ok")

**Uso:** Health checks en orquestadores (Kubernetes) y load balancers

**Respuesta exitosa (200 OK):**
```json
{
    "status": "ok"
}
```

### POST /items

```python
async def create_or_update_item(item: ItemCreate, db: Session = Depends(get_db))
```

**Propósito:** Crear nuevo producto o actualizar existente (upsert)

**Validaciones esperadas:**
1. Validar que 'title' sea único en BD (no duplicados para diferente 'id')
2. Si violación de unicidad → HTTPException(409 Conflict)
3. Si 'id' existe → Actualizar campo 'title'
4. Si 'id' no existe → Crear nuevo registro

**Body requerido:**
```json
{
    "id": "MLA123456",
    "title": "Celular Samsung Galaxy S23"
}
```

**Respuesta (201 Created):**
```json
{
    "id": "MLA123456",
    "title": "Celular Samsung Galaxy S23",
    "message": "Item creado/actualizado correctamente."
}
```

### POST /matches

```python
async def create_match_from_texts(match_data: MatchCreate)
```

**Propósito:** Comparar dos textos, calcular similitud y persistir match

**Implementación esperada:**
1. Calcular score de similitud entre text_1 y text_2 (ej: coseno, Levenshtein)
2. Crear dos nuevos items en BD con títulos = textos proporcionados
3. Crear nuevo match en tabla matches con IDs de items y score calculado
4. Retornar match completo con IDs generados

**Body requerido:**
```json
{
    "text_1": "Smartphone de última generación",
    "text_2": "Teléfono móvil avanzado"
}
```

**Respuesta (201 Created):**
```json
{
    "id": 1,
    "id_item_1": "MLA_NEW_1",
    "title_item_1": "Smartphone de última generación",
    "id_item_2": "MLA_NEW_2",
    "title_item_2": "Teléfono móvil avanzado",
    "score": 0.88,
    "status": "en progreso"
}
```

### POST /matches/compare-by-ids

```python
async def compare_items_by_ids(compare_data: MatchCompare)
```

**Propósito:** Comparar dos items existentes por sus IDs

**Lógica esperada:**
1. Buscar match previo entre id_a e id_b
2. Si existe y status="positivo" → Retornar sin cambios (evitar recálculo)
3. Si existe otros status o no existe:
     - Obtener titles de ambos items desde BD
     - Recalcular score de similitud
     - Actualizar o crear match con nuevo score
4. Retornar match actualizado

**Nota:** Evitar recálculo innecesario para matches confirmados (positivos)

**Body requerido:**
```json
{
    "id_a": "MLA123456",
    "id_b": "MLA654321"
}
```

**Respuesta (200 OK):**
```json
{
    "id": 2,
    "id_item_1": "MLA123456",
    "title_item_1": "Título del Item A",
    "id_item_2": "MLA654321",
    "title_item_2": "Título del Item B",
    "score": 0.92,
    "status": "positivo"
}
```

### GET /matches/{match_id}

```python
async def get_match_by_id(match_id: int = Path(..., description="..."))
```

**Propósito:** Recuperar información completa de un match específico

**Parámetros path:**
- `match_id` (int): ID único del match a consultar (validado como int)

**Implementación esperada:**
1. Buscar match en tabla matches WHERE id = match_id
2. Si no existe → HTTPException(404 Not Found)
3. Si existe → Retornar objeto MatchResponse completo

**Ejemplo:** `GET /matches/101`

**Respuesta (200 OK):**
```json
{
    "id": 101,
    "id_item_1": "MLA123456",
    "title_item_1": "Celular Samsung Galaxy S23",
    "id_item_2": "MLA654321",
    "title_item_2": "Samsung S23 128GB",
    "score": 0.95,
    "status": "positivo"
}
```

**Error (404 Not Found):**
```json
{
    "detail": "Match no encontrado."
}
```

### GET /tables/{table_name}/colnames

```python
async def get_table_header(table_name: str, db: Session = Depends(get_db))
```

**Propósito:** Introspección de estructura de tabla (obtener nombres de columnas)

**Parámetros path:**
- `table_name` (str): Nombre de tabla a inspeccionar

**Implementación:**
1. Crear inspector de metadatos: `inspector = inspect(engine)`
2. Validar existencia: `inspector.has_table(table_name)`
3. Si no existe → HTTPException(404) con detalle descriptivo
4. Obtener columnas: `inspector.get_columns(table_name)`
5. Extraer nombres: `[col['name'] for col in columns_metadata]`
6. Retornar TableHeaderResponse(table_name, column_names)

**Manejo de excepciones:**
- HTTPException: Re-lanzar (errores controlados, ej: 404)
- Exception general: Loguear y lanzar HTTPException(500)

**Ejemplo:** `GET /tables/items/colnames`

**Respuesta (200 OK):**
```json
{
    "table_name": "items",
    "columns": ["id", "title", "created_at", "updated_at"]
}
```

**Error (404 Not Found):**
```json
{
    "detail": "La tabla 'items' no existe en el esquema actual de la SIC."
}
```

### GET /tables/{table_name}/header

**Parámetros:**
- `table_name` (str): Nombre de tabla a samplear
- `db` (Session): Sesión de BD activa (inyectado)

**Propósito:** Obtener muestra de datos (primeras 3 filas) de tabla especificada

**Implementación:**
1. Validar tabla: `inspector.has_table(table_name)`
2. Si no existe → HTTPException(404)
3. Ejecutar: `SELECT * FROM {table_name} LIMIT 3`
4. Mapear resultados a diccionarios: `dict(row._mapping)`
5. Retornar lista de dicts (serializable a JSON)

**Consideraciones de seguridad:**
- Usar `text()` con parámetros es más seguro que f-string directo (SQL injection)
- Limitado a 3 filas (evita transferencia de datos innecesaria)

**Manejo de excepciones:**
- HTTPException: Re-lanzar (errores esperados)
- Exception general: Loguear y HTTPException(500)

**Ejemplo:** `GET /tables/items/header`

**Respuesta (200 OK):**
```json
[
    {
        "id": "MLA123456",
        "title": "Celular Samsung Galaxy S23",
        "created_at": "2024-01-15"
    },
    {
        "id": "MLA654321",
        "title": "Samsung S23 128GB",
        "created_at": "2024-01-16"
    },
    {
        "id": "MLA789012",
        "title": "Galaxy S23 Ultra",
        "created_at": "2024-01-17"
    }
]
```

**Error (500 Internal Server Error):**
```json
{
    "detail": "Fallo en la conexión con la base de datos institucional."
}
```

### POST /matches/backup-and-reset

```python
async def backup_and_reset_matches()
```

**Propósito:** Respaldar tabla matches y vaciarla (operación destructiva)

**Implementación esperada:**
1. Iniciar transacción explícita
2. Copiar todo de matches → matches_backup (INSERT INTO ... SELECT *)
3. Eliminar todo de matches (TRUNCATE TABLE matches)
4. Hacer commit de transacción
5. Retornar BackupResponse(message, records_moved=cantidad_movida)

**Propiedades transaccionales (ACID):**
- **Atomicidad:** Backup y reset se hacen juntos o ninguno
- **Consistencia:** Si hay error, rollback automático
- **Aislamiento:** Otros procesos ven snapshot consistente
- **Durabilidad:** Datos en matches_backup persistidos en BD

**Uso:** Limpiar tabla matches después de análisis/auditoría

**⚠️ Advertencia:** Operación NO reversible (requiere restauración manual desde backup)

**Respuesta (200 OK):**
```json
{
    "message": "Backup completado y tabla 'matches' reseteada.",
    "records_moved": 150
}
```

---

## Sección 7: Arquitectura y Patrones

### Patrón MVC (Model-View-Controller)

- **Model:** Schemas Pydantic (ItemCreate, MatchResponse, etc)
- **View:** Response models (JSON serialización automática)
- **Controller:** Funciones de endpoints (@app.post, @app.get)

### Inyección de Dependencias (FastAPI)

- `get_db()` proporciona sesiones reutilizables vía `Depends()`
- Desacoplamiento entre endpoints y gestión de BD
- Cleanup automático (`close()`) al finalizar request

### Validación en Capas

1. **Capa 1:** Pydantic valida tipos y estructura (BaseModel)
2. **Capa 2:** Path parameters validados (Path(...))
3. **Capa 3:** Lógica de negocio (verificar uniqueness, relaciones, etc)

### Seguridad

- Clúster privado AKS para ejecución (no expuesto públicamente)
- Variables de entorno para credenciales (DATABASE_URL)
- SQL parameterizado (`text()`) contra SQL injection
- Validación de entrada en todas las capas

---

## Sección 8: Notas de Implementación

### Pendientes Técnicos

1. **Import no utilizado:** El import de `NoSuchTableError` no se utiliza actualmente
     - → Considerar remover o usar explícitamente en try-except de métodos de BD

2. **Lógica de negocio incompleta:** Marcada con TODO en el código
     - → Cada endpoint tiene comentarios detallados de implementación pendiente

3. **Mock data en respuestas:** Endpoints usan valores hardcoded
     - → Al implementar, reemplazar con consultas reales a BD

4. **Validación de relaciones:** No implementada
     - → Agregar checks de existencia de items antes de crear matches

### Mejoras de Código

5. **Logging básico:** Actualmente usa print statements
     - → Integrar con sistema de logging estructurado (logging module, Sentry)

6. **Transacciones explícitas:** Solo mencionadas en backup endpoint
     - → Considerar usar context managers de SQLAlchemy en otros endpoints
