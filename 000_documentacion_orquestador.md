# MELI CHALLENGE API - DOCUMENTACIÓN COMPLETA DEL MÓDULO MAIN.PY

## Descripción General

Módulo principal de la API FastAPI para el Desafío de Desarrollo Op 2 - AA&ML de MercadoLibre. Proporciona endpoints RESTful para gestión de items, comparación de similitudes entre textos y productos, y operaciones sobre matches con múltiples algoritmos de NLP.

- **Autor:** https://github.com/anguihero & https://www.linkedin.com/in/amms1989/
- **Versión:** 2.1.0
- **Fecha:** 2026/2/18

---

## Sección 1: Importaciones y Dependencias

### Framework Core
- **FastAPI:** Framework web para construir APIs REST asincrónicas
- **HTTPException, status:** Excepciones HTTP y códigos de estado
- **Path, Query, Depends:** Validación de parámetros e inyección de dependencias

### Pydantic & Validación
- **BaseModel, Field:** Schemas de validación de datos con tipos y documentación
- **Enum:** Enumeraciones para valores discretos (StatusEnum)

### Type Hints
- **List, Dict, Any, Optional:** Anotaciones de tipo genéricas

### Base de Datos (SQLAlchemy)
- **create_engine:** Constructor de motores de conexión a PostgreSQL
- **text, inspect:** Consultas SQL parametrizadas e introspección de metadatos
- **Session, sessionmaker:** Contexto de sesiones transaccionales

### Algoritmos de Similitud NLP
- **Levenshtein:** Distancia de edición (edit distance)
- **SequenceMatcher (difflib):** Algoritmo Gestalt Pattern Matching
- **Counter (collections):** Contador de tokens para similitud de coseno
- **sqrt (math):** Cálculo de normas vectoriales

### Utilidades
- **os:** Acceso a variables de entorno del sistema
- **datetime:** Generación de timestamps ISO 8601

---

## Sección 2: Enumeraciones (Enums)

### StatusEnum

```python
class StatusEnum(str, Enum):
    positivo = "positivo"
    en_progreso = "en progreso"
    negativo = "negativo"
```

Enumeración que define estados válidos de match en el sistema.

**Valores:**
- `"positivo"`: Match confirmado como similar (score >= threshold)
- `"en progreso"`: Match bajo evaluación/pendiente
- `"negativo"`: Match confirmado como no similar (score < threshold)

**Propósito:** Garantizar consistencia de datos y validar estados en BD

---

## Sección 3: Modelos Pydantic (Schemas de Validación)

### ItemCreate
```python
class ItemCreate(BaseModel):
    id: int = Field(..., description="Identificador único del producto")
    title: str = Field(..., description="Título del producto")
```
Schema para validar entrada al crear items. Convertible a entero.

### ItemResponse
```python
class ItemResponse(ItemCreate):
    message: str = "Item creado/actualizado correctamente."
```
Respuesta con confirmación de operación.

### MatchCreate
```python
class MatchCreate(BaseModel):
    text_1: str = Field(..., description="Primer texto a comparar")
    text_2: str = Field(..., description="Segundo texto a comparar")
```
Input para comparación de dos textos arbitrarios.

### MatchCompare
```python
class MatchCompare(BaseModel):
    id_a: int = Field(..., description="ID del primer item")
    id_b: int = Field(..., description="ID del segundo item")
```
Input para comparación de items existentes por ID.

### MatchResponse
```python
class MatchResponse(BaseModel):
    id: int
    id_item_1: str
    title_item_1: str
    id_item_2: str
    title_item_2: str
    score: float  # Rango [0.0, 1.0]
    status: StatusEnum
```
Respuesta estándar para queries sobre matches.

### HealthResponse
```python
class HealthResponse(BaseModel):
    status: str = "ok"
    message: Optional[str] = "Conectividad verificada exitosamente"
```
Respuesta simple de health check.

### TableHeaderResponse
```python
class TableHeaderResponse(BaseModel):
    table_name: str
    columns: list[str]
```
Respuesta de introspección de metadatos de tabla.

### BackupResponse
```python
class BackupResponse(BaseModel):
    message: str
    records_moved: int
```
Confirmación de operación de backup con cantidad de registros.

---

## Sección 4: Configuración de Base de Datos

### DATABASE_URL
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/meli_app_db")
```
Cadena de conexión a PostgreSQL desde variables de entorno.

### engine
Motor SQLAlchemy que gestiona pool de conexiones (5 por defecto, +10 overflow).

### SessionLocal
```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```
Factory de sesiones para BD.

### get_db()
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
Generador que proporciona sesiones reutilizables como dependencias (context manager pattern).

### init_db()
```python
def init_db(database_url: str = None):
    target_url = database_url or DATABASE_URL
    _engine = create_engine(target_url)
    _SessionLocal = sessionmaker(bind=_engine)
    _db = _SessionLocal()
    return _engine, _db
```
Función de inicialización que evita shadowing de variables globales.

---

## Sección 5: Servicio de Similitud (SimilarityService)

Clase con métodos estáticos para calcular similitud entre textos usando 4 algoritmos diferentes.

### calculate_similarity_Levenshtein()
Distancia de edición normalizada. Métrica: 1 - (distancia / max_len)

### calculate_similarity_SequenceMatcher()
Patrón Gestalt de difflib. Ratio de coincidencia directa.

### calculate_similarity_Jaccard()
Similitud sobre términos tokenizados: |A ∩ B| / |A ∪ B|

### calculate_similarity_Cosine()
Similitud de coseno con frecuencia de tokens y filtro de stopwords:
```
cos(A,B) = (A·B) / (||A|| × ||B||)
```

### calculate_similarity()
Dispatcher que selecciona algoritmo según parámetro `method`.

---

## Sección 6: Función test_match_existence()

Núcleo de lógica de matching. Evalúa existencia y calcula similitud entre dos items.

**Flujo Principal:**

1. **Validación:** Verifica IDs diferentes y existencia en BD
2. **Búsqueda Bidireccional:** Consulta matches previos (ambas direcciones)
3. **Evaluación de Estado:**
   - Si match POSITIVO → Retorna resultado sin recalcular
   - Si match NEGATIVO → Recalcula y actualiza
   - Si no existe → Calcula y crea nuevo
4. **Persistencia:** Inserta/actualiza registros con timestamps ISO
5. **Respuesta Estructurada:** Mensaje y resultado con metadatos

**Parámetros:**
- `ids`: Lista [id_a, id_b]
- `db`: Sesión SQLAlchemy
- `threshold`: Umbral para estado positivo (default 0.5)
- `metodo_seleccionado`: Algoritmo NLP (default "sequencematcher")

**Retorna:**
```python
{
    "mensaje": {...},
    "resultado": {...}
}
```

---

## Sección 7: Función insert_item()

```python
def insert_item(db: Session, id_item: int, title: str) -> str
```

Inserta nuevo item en tabla `items`. Valida no-duplicados antes de insertar.

**Retorna:** Mensaje de confirmación o error.

---

## Sección 8: Instanciación de FastAPI

```python
app = FastAPI(
    title="MELI Challenge API",
    description="...",
    version="1.0.0"
)
```

Crea instancia con documentación automática en `/docs` y `/redoc`.

---

## Sección 9: Endpoints (Rutas HTTP)

### GET /health
```python
async def health_check(db: Session = Depends(get_db)) -> HealthResponse
```

**Propósito:** Verificar disponibilidad de API y BD.

**Implementación:**
- Ejecuta `SELECT 1` en BD
- Si falla → HTTPException(503 Service Unavailable)
- Si éxito → HealthResponse(status="ok")

**Respuesta (200 OK):**
```json
{
    "status": "ok",
    "message": "Conectividad con la base de datos verificada exitosamente"
}
```

### POST /matches/testing-text
```python
async def test_match_from_texts(
    match_data: MatchCreate,
    UMBRAL: float = 0.5,
    method: str = "levenshtein"
) -> MatchResponse
```

**Propósito:** Comparar dos textos SIN persistir en BD (testing).

**Comportamiento:**
- Genera IDs ficticios basados en timestamp
- Calcula score con algoritmo seleccionado
- Determina estado según UMBRAL
- No realiza llamadas externas ni inserta datos

**Body:**
```json
{
    "text_1": "Smartphone Samsung Galaxy S23",
    "text_2": "Celular Samsung S23"
}
```

**Query Parameters:**
- `UMBRAL` (float): Umbral de positividad (default 0.5)
- `method` (str): "levenshtein" | "sequencematcher" | "jaccard" | "cosine"

**Respuesta (201 Created):**
```json
{
    "id": 1707847514000,
    "id_item_1": "MLA_TEXT_1707847514_1",
    "title_item_1": "Smartphone Samsung Galaxy S23",
    "id_item_2": "MLA_TEXT_1707847514_2",
    "title_item_2": "Celular Samsung S23",
    "score": 0.86957,
    "status": "positivo"
}
```

### POST /matches/compare-by-ids
```python
async def compare_items_by_ids(
    id_a: int,
    id_b: int,
    UMBRAL: float = 0.5,
    db: Session = Depends(get_db)
)
```

**Propósito:** Comparar dos items existentes en BD por IDs.

**Lógica:**
- Busca match previo bidireccionally
- Si positivo → Retorna sin recalcular
- Si negativo/no existe → Recalcula y persiste
- Usa algoritmo SequenceMatcher por defecto

**Query Parameters:**
- `id_a` (int): ID primer item
- `id_b` (int): ID segundo item
- `UMBRAL` (float): Threshold de positividad

**Respuesta (200 OK):**
```json
{
    "mensaje": {
        "ids_consultados": [123, 456],
        "match_encontrado": "Sí",
        "estado_match_encontrado": "POSITIVO",
        "accion_recomendada": "✅ MATCH POSITIVO ENCONTRADO..."
    },
    "resultado": {
        "id_item_1": "123",
        "title_item_1": "Celular Samsung Galaxy S23",
        "id_item_2": "456",
        "title_item_2": "Samsung S23 128GB",
        "score": 0.92,
        "status": "positivo",
        "created_at": "2026-02-18T21:55:14.036671+00:00",
        "updated_at": "2026-02-18T21:55:14.036671+00:00"
    }
}
```

### GET /tables/{table_name}/colnames
```python
async def get_table_header(
    table_name: str,
    db: Session = Depends(get_db)
) -> TableHeaderResponse
```

**Propósito:** Obtener nombres de columnas de tabla.

**Implementación:**
1. Crea inspector: `inspector = inspect(engine)`
2. Valida existencia: `inspector.has_table(table_name)`
3. Extrae nombres: `[col['name'] for col in columns]`
4. Si no existe → HTTPException(404)

**Ejemplo:** `GET /tables/items/colnames`

**Respuesta (200 OK):**
```json
{
    "table_name": "items",
    "columns": ["id", "id_item", "title", "created_at", "updated_at"]
}
```

**Error (404 Not Found):**
```json
{
    "detail": "La tabla 'items' no existe en el esquema actual"
}
```

### GET /tables/{table_name}/header
```python
async def get_table_sample(
    table_name: str = Path(...),
    rows: int = Query(3, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]
```

**Propósito:** Obtener muestra de datos (primeras N filas) de tabla.

**Parámetros:**
- `table_name` (str): Nombre de tabla
- `rows` (int): Número de filas a retornar (1-100, default 3)

**Implementación:**
1. Valida tabla con inspector
2. Verifica columna `updated_at` para ordenamiento
3. Ejecuta `SELECT * LIMIT :limit` con parámetros seguros
4. Retorna lista de diccionarios (JSON)

**Ejemplo:** `GET /tables/items/header?rows=5`

**Respuesta (200 OK):**
```json
[
    {
        "id": 1,
        "id_item": "123456",
        "title": "Celular Samsung Galaxy S23",
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00"
    },
    {
        "id": 2,
        "id_item": "654321",
        "title": "Samsung S23 128GB",
        "created_at": "2024-01-16T15:20:00",
        "updated_at": "2024-01-16T15:20:00"
    }
]
```

### POST /tables/add-items
```python
async def create_or_update_item(
    item: ItemCreate,
    db: Session = Depends(get_db)
) -> ItemResponse
```

**Propósito:** Crear o actualizar item en tabla `items`.

**Validaciones:**
- Convierte ID string → int
- Valida no-duplicados (evita repetidos)
- Inserta o retorna error si existe

**Body:**
```json
{
    "id": 123456,
    "title": "Celular Samsung Galaxy S23"
}
```

**Respuesta (201 Created):**
```json
{
    "id": 123456,
    "title": "Celular Samsung Galaxy S23",
    "message": "✅ Item insertado exitosamente: id=1, id_item=123456, title='Celular Samsung Galaxy S23'"
}
```

**Error (400 Bad Request):**
```json
{
    "detail": "El ID debe ser un número entero válido"
}
```

---

## Sección 10: Arquitectura y Patrones

### Patrón MVC
- **Model:** Schemas Pydantic (ItemCreate, MatchResponse)
- **View:** Response JSON (FastAPI auto-serializa)
- **Controller:** Funciones endpoint (@app.post, @app.get)

### Inyección de Dependencias
- `Depends(get_db)` proporciona sesiones reutilizables
- Cleanup automático (`finally db.close()`)
- Desacoplamiento BD↔lógica

### Validación en Capas
1. **Pydantic:** Tipos y estructura
2. **Path/Query:** Parámetros de ruta
3. **Business Logic:** Verificación de relaciones, threshold, etc

### Seguridad
- Clúster AKS privado
- Variables de entorno (DATABASE_URL)
- SQL parametrizado con `text()`
- Validación de entrada en todas las capas

### Algoritmos NLP
Soporte para 4 métodos de similitud con preprocesamiento:
- **Levenshtein:** Distancia de edición
- **SequenceMatcher:** Pattern matching (Gestalt)
- **Jaccard:** Similitud de tokens
- **Cosine:** Similitud vectorial (robusto para vocabulario distinto)

---

## Sección 11: Notas de Implementación

### Cambios en v2.1.0
1. **SimilarityService:** Clase con 4 algoritmos configurable
2. **test_match_existence():** Función core robusta con lógica bidireccional
3. **Multiple endpoints:** Comparación de textos y IDs separadas
4. **Timestamps ISO 8601:** datetime en lugar de strings
5. **Query parameters:** method y UMBRAL configurables

### Pendientes Técnicos
- Logging estructurado (actualmente print)
- Índices de BD en columnas de búsqueda
- Caché de matches positivos
- Rate limiting en endpoints de cálculo

### Mejoras Propuestas
- Integración con API de Mercado Libre (MELI SDK)
- Batch processing para múltiples comparaciones
- Webhooks para notificaciones de matches
- Métricas de precisión de algoritmos (precision/recall)

