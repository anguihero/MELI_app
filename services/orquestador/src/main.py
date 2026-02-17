from fastapi import FastAPI, HTTPException, status, Path
from pydantic import BaseModel, Field
from enum import Enum
from typing import List

# --- Enums y Modelos de Datos (Schemas Pydantic) ---

class StatusEnum(str, Enum):
    """Enumeración para los estados de un match."""
    positivo = "positivo"
    en_progreso = "en progreso"
    negativo = "negativo"

class ItemCreate(BaseModel):
    """Schema para la creación de un nuevo item."""
    id: str = Field(..., description="Identificador único del producto.", example="MLA123456")
    title: str = Field(..., description="Título del producto.", example="Celular Samsung Galaxy S23")

class ItemResponse(ItemCreate):
    """Schema para la respuesta al crear un item."""
    message: str = "Item creado/actualizado correctamente."

class MatchCreate(BaseModel):
    """Schema para la creación de un match a partir de dos textos."""
    text_1: str = Field(..., description="Primer texto a comparar.", example="Smartphone de última generación")
    text_2: str = Field(..., description="Segundo texto a comparar.", example="Teléfono móvil avanzado")

class MatchCompare(BaseModel):
    """Schema para la comparación de dos items por sus IDs."""
    id_a: str = Field(..., description="ID del primer item.", example="MLA123456")
    id_b: str = Field(..., description="ID del segundo item.", example="MLA654321")

class MatchResponse(BaseModel):
    """Schema para la respuesta de un match."""
    id: int = Field(..., description="ID único del match.", example=101)
    id_item_1: str = Field(..., description="ID del primer producto.", example="MLA123456")
    title_item_1: str = Field(..., description="Título del primer producto.", example="Celular Samsung Galaxy S23")
    id_item_2: str = Field(..., description="ID del segundo producto.", example="MLA654321")
    title_item_2: str = Field(..., description="Título del segundo producto.", example="Samsung S23 128GB")
    score: float = Field(..., description="Puntuación de similitud del match.", example=0.95)
    status: StatusEnum = Field(..., description="Estado del match.", example=StatusEnum.positivo)

class HealthResponse(BaseModel):
    """Schema para la respuesta del health check."""
    status: str = "ok"

class TableHeaderResponse(BaseModel):
    """Schema para la respuesta de las columnas de una tabla."""
    table_name: str
    columns: List[str]

class BackupResponse(BaseModel):
    """Schema para la respuesta del proceso de backup."""
    message: str
    records_moved: int

# --- Aplicación FastAPI ---

app = FastAPI(
    title="MELI Challenge API",
    description=(
        "API para el Desafío de Desarrollo Op 2 - AA&ML de MercadoLibre.\n\n"
        "Desarrollador: Andrés Muñoz\n"
        "Propósito: Esta API fue creada con un toque lúdico y con el objetivo de demostrar suficiencia técnica en el desarrollo de microservicios, manejo de datos y diseño de APIs RESTful.\n\n"
        "Descripción: La API está diseñada para resolver un desafío técnico de MercadoLibre, específicamente en el contexto de AA&ML (Aprendizaje Automático y Analítica Avanzada). Proporciona endpoints para la gestión de items, comparación de similitudes entre textos y productos, y operaciones relacionadas con la tabla de matches.\n\n"
        "Características principales:\n"
        "1. **Gestión de Items**:\n"
        "   - Crear o actualizar registros de productos.\n"
        "   - Validación de unicidad en los títulos de los productos.\n"
        "2. **Comparación de Similitudes**:\n"
        "   - Comparación de textos para calcular similitudes y generar matches.\n"
        "   - Comparación de productos existentes por sus IDs.\n"
        "3. **Operaciones sobre Matches**:\n"
        "   - Recuperación de información de matches específicos.\n"
        "   - Respaldo y reseteo de la tabla de matches.\n"
        "4. **Salud y Metadatos**:\n"
        "   - Verificación de la conectividad con la base de datos.\n"
        "   - Obtención de nombres de columnas y muestras de datos de tablas específicas.\n"
        "5. **Diseño Modular y Extensible**:\n"
        "   - Uso de FastAPI para un desarrollo rápido y eficiente.\n"
        "   - Modelos de datos definidos con Pydantic para validación robusta.\n"
        "   - Enumeraciones para estados de matches, asegurando consistencia en los datos.\n\n"
        "Notas adicionales:\n"
        "- Este proyecto incluye lógica simulada (mock) para facilitar la demostración de funcionalidades en ausencia de una base de datos real.\n"
        "- Cada endpoint está documentado con descripciones detalladas y ejemplos de uso.\n"
        "- El código está diseñado para ser fácilmente extensible y adaptable a escenarios reales.\n\n"
        "¡Bienvenido a este viaje técnico lleno de aprendizaje y diversión!"
    ),
    version="1.0.0",
)

# --- Endpoints ---

@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_item(item: ItemCreate):
    """
    Crea un nuevo registro en la tabla 'items' o lo actualiza si ya existe.
    
    - **Valida** que el 'title' sea único en la base de datos.
    - Si el `id` ya existe, se podría actualizar el `title` (lógica a definir).
    """
    # TODO: Implementar lógica de negocio
    # 1. Conectar a la DB.
    # 2. Verificar si el `title` ya existe para otro `id`. Si es así, lanzar HTTPException 409 (Conflict).
    # 3. Usar un "upsert": si el `id` existe, actualizar; si no, crear.
    print(f"Recibido item: {item.id} - {item.title}")
    return ItemResponse(id=item.id, title=item.title)

@app.post("/matches", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match_from_texts(match_data: MatchCreate):
    """
    Recibe dos textos, calcula su similitud y persiste el resultado como un nuevo match.
    
    - La lógica de cálculo de similitud no se implementa aquí.
    - Se asume que los items correspondientes a los textos no existen previamente.
    """
    # TODO: Implementar lógica de negocio
    # 1. Calcular el `score` de similitud entre `text_1` y `text_2`.
    # 2. Crear dos nuevos `items` en la DB con los títulos proporcionados.
    # 3. Crear un nuevo `match` en la DB con los IDs de los nuevos items y el score.
    # 4. Retornar el match creado.
    print(f"Comparando textos: '{match_data.text_1}' vs '{match_data.text_2}'")
    return MatchResponse(
        id=1,
        id_item_1="MLA_NEW_1", title_item_1=match_data.text_1,
        id_item_2="MLA_NEW_2", title_item_2=match_data.text_2,
        score=0.88, # Score de ejemplo
        status=StatusEnum.en_progreso
    )

@app.post("/matches/compare-by-ids", response_model=MatchResponse)
async def compare_items_by_ids(compare_data: MatchCompare):
    """
    Compara dos items existentes por sus IDs y actualiza o crea un match.
    
    - Si ya existe un match **POSITIVO** entre los IDs, no se hace nada.
    - Si el match existe pero con otro estado, se recalcula y actualiza.
    - Si no existe, se crea uno nuevo.
    """
    # TODO: Implementar lógica de negocio
    # 1. Buscar un match existente entre `id_a` y `id_b`.
    # 2. Si existe y es "positivo", retornarlo sin cambios.
    # 3. Si existe pero no es "positivo", o si no existe:
    #    a. Obtener los `titles` de los items desde la DB.
    #    b. Recalcular el `score`.
    #    c. Actualizar o crear el match.
    # 4. Retornar el match.
    print(f"Comparando por IDs: {compare_data.id_a} vs {compare_data.id_b}")
    return MatchResponse(
        id=2,
        id_item_1=compare_data.id_a, title_item_1="Título del Item A",
        id_item_2=compare_data.id_b, title_item_2="Título del Item B",
        score=0.92, # Score recalculado
        status=StatusEnum.positivo
    )

@app.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match_by_id(match_id: int = Path(..., description="ID único del match a recuperar.")):
    """
    Recupera la información de un match específico por su ID.
    """
    # TODO: Implementar lógica de negocio
    # 1. Buscar el match en la DB por `match_id`.
    # 2. Si no se encuentra, lanzar HTTPException 404 (Not Found).
    # 3. Retornar los datos del match.
    print(f"Buscando match con ID: {match_id}")
    if match_id == 999: # Simulación de no encontrado
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match no encontrado.")
    
    return MatchResponse(
        id=match_id,
        id_item_1="MLA123456", title_item_1="Celular Samsung Galaxy S23",
        id_item_2="MLA654321", title_item_2="Samsung S23 128GB",
        score=0.95,
        status=StatusEnum.positivo
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Verifica la conectividad con la base de datos.
    
    Retorna un status "ok" si la conexión es exitosa.
    """
    # TODO: Implementar lógica de negocio
    # 1. Intentar hacer una consulta simple a la DB (ej: `SELECT 1`).
    # 2. Si falla, lanzar HTTPException 503 (Service Unavailable).
    # 3. Si es exitosa, retornar el status "ok".
    return HealthResponse(status="ok")

@app.get("/tables/{table_name}/colnames", response_model=TableHeaderResponse)
async def get_table_header(table_name: str = Path(..., description="Nombre de la tabla a consultar.")):
    """
    Obtiene los nombres de las columnas (cabecera) de una tabla específica.
    """
    # TODO: Implementar lógica de negocio
    # 1. Conectar a la DB.
    # 2. Usar introspección de SQLAlchemy o una consulta SQL para obtener las columnas.
    # 3. Validar que la tabla exista. Si no, HTTPException 404.
    # 4. Retornar la lista de columnas.
    print(f"Obteniendo cabecera de la tabla: {table_name}")
    
    mock_headers = {
        "items": ["id", "title", "created_at", "updated_at"],
        "matches": ["id", "id_item_1", "title_item_1", "id_item_2", "title_item_2", "score", "status", "created_at", "updated_at"]
    }
    
    if table_name not in mock_headers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tabla '{table_name}' no encontrada.")
        
    return TableHeaderResponse(table_name=table_name, columns=mock_headers[table_name])

@app.get("/tables/{table_name}/header", response_model=List[dict])
async def get_table_sample(table_name: str = Path(..., description="Nombre de la tabla a consultar.")):
    """
    Obtiene los primeros 3 registros de una tabla específica.
    """
    # TODO: Implementar lógica de negocio
    # 1. Conectar a la DB.
    # 2. Validar que la tabla exista. Si no, HTTPException 404.
    # 3. Hacer un `SELECT *` y limitar a los primeros 3 registros.
    # 4. Retornar los registros como una lista de diccionarios.
    print(f"Obteniendo los primeros 3 registros de la tabla: {table_name}")
    
    mock_data = {
        "items": [
            {"id": "MLA123456", "title": "Celular Samsung Galaxy S23", "created_at": "2023-01-01", "updated_at": "2023-01-02"},
            {"id": "MLA654321", "title": "Samsung S23 128GB", "created_at": "2023-01-03", "updated_at": "2023-01-04"},
            {"id": "MLA789012", "title": "iPhone 14 Pro", "created_at": "2023-01-05", "updated_at": "2023-01-06"}
        ],
        "matches": [
            {"id": 1, "id_item_1": "MLA123456", "title_item_1": "Celular Samsung Galaxy S23", "id_item_2": "MLA654321", "title_item_2": "Samsung S23 128GB", "score": 0.95, "status": "positivo", "created_at": "2023-01-01", "updated_at": "2023-01-02"},
            {"id": 2, "id_item_1": "MLA789012", "title_item_1": "iPhone 14 Pro", "id_item_2": "MLA654321", "title_item_2": "Samsung S23 128GB", "score": 0.85, "status": "en progreso", "created_at": "2023-01-03", "updated_at": "2023-01-04"},
            {"id": 3, "id_item_1": "MLA123456", "title_item_1": "Celular Samsung Galaxy S23", "id_item_2": "MLA789012", "title_item_2": "iPhone 14 Pro", "score": 0.75, "status": "negativo", "created_at": "2023-01-05", "updated_at": "2023-01-06"}
        ]
    }
    
    if table_name not in mock_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tabla '{table_name}' no encontrada.")
        
    return mock_data[table_name][:3]
async def get_table_header(table_name: str = Path(..., description="Nombre de la tabla a consultar.")):
    """
    Obtiene los nombres de las columnas (cabecera) de una tabla específica.
    """
    # TODO: Implementar lógica de negocio
    # 1. Conectar a la DB.
    # 2. Usar introspección de SQLAlchemy o una consulta SQL para obtener las columnas.
    # 3. Validar que la tabla exista. Si no, HTTPException 404.
    # 4. Retornar la lista de columnas.
    print(f"Obteniendo cabecera de la tabla: {table_name}")
    
    mock_headers = {
        "items": ["id", "title", "created_at", "updated_at"],
        "matches": ["id", "id_item_1", "title_item_1", "id_item_2", "title_item_2", "score", "status", "created_at", "updated_at"]
    }
    
    if table_name not in mock_headers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tabla '{table_name}' no encontrada.")
        
    return TableHeaderResponse(table_name=table_name, columns=mock_headers[table_name])



@app.post("/matches/backup-and-reset", response_model=BackupResponse)
async def backup_and_reset_matches():
    """
    Realiza un backup de la tabla 'matches' y luego la vacía.
    
    - Mueve todos los datos de la tabla `matches` a `matches_backup`.
    - Elimina todos los registros de la tabla `matches`.
    """
    # TODO: Implementar lógica de negocio
    # 1. Iniciar una transacción.
    # 2. Copiar todos los datos de `matches` a `matches_backup`.
    # 3. Eliminar todos los datos de `matches`.
    # 4. Hacer commit de la transacción.
    # 5. Retornar el número de registros movidos.
    print("Iniciando proceso de backup y reseteo de matches.")
    return BackupResponse(message="Backup completado y tabla 'matches' reseteada.", records_moved=150)
