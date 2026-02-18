import os
from datetime import datetime
from enum import Enum
from math import sqrt
from collections import Counter
from typing import List, Dict, Any, Optional

# --- 1. Framework Core & HTTP ---
from fastapi import FastAPI, HTTPException, status, Path, Depends

# --- 2. Validación de Esquemas (Pydantic) ---
from pydantic import BaseModel, Field

# --- 3. Base de Datos y Persistencia (SQLAlchemy) ---
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session, sessionmaker

# --- 4. Algoritmos de Similitud ---
import Levenshtein                      # Distancia de edición
from difflib import SequenceMatcher       # Algoritmo Gestalt Pattern Matching

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

# Definición del modelo de respuesta
class TableHeaderResponse(BaseModel):
    table_name: str
    columns: list[str]

# # Dependencia para obtener la sesión de DB (Configurar vía variables de entorno)
# # El Hub central de infraestructura gestiona estas credenciales [cite: 52, 142]
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/meli_app_db")
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# def get_db():
#     db = Session(engine)
#     try:
#         yield db
#     finally:
#         db.close()

# def init_db(database_url: str = None):
#     url = database_url or os.getenv("DATABASE_URL", DATABASE_URL)
#     engine = create_engine(url)
#     db = next(get_db())
#     return engine, db, get_db

# engine, db, get_db = init_db()


# 1. Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/meli_app_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. El generador de sesiones (NO lo sobrescribas después)
def get_db():
    """Dependencia para inyectar la sesión en los endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. Función de inicialización corregida
def init_db(database_url: str = None):
    # Usamos nombres distintos para evitar conflictos de alcance (shadowing)
    target_url = database_url or DATABASE_URL
    _engine = create_engine(target_url)
    
    # Creamos una sesión única para la inicialización
    _SessionLocal = sessionmaker(bind=_engine)
    _db = _SessionLocal()
    
    # Retornamos solo lo necesario
    return _engine, _db

# 4. Ejecución (Sin destruir la función get_db)
# IMPORTANTE: Aquí solo recibimos engine y db. 
# get_db se queda como la función definida arriba.
engine, db = init_db()

class BackupResponse(BaseModel):
    """Schema para la respuesta del proceso de backup."""
    message: str
    records_moved: int


class SimilarityService:
    """
    Capa de servicio para algoritmos de procesamiento de lenguaje natural (NLP).
    Implementa criterios de aceptación para puntajes entre 0 y 1[cite: 585, 961].
    """
    
    @staticmethod
    def calculate_similarity_Levenshtein(text1: str, text2: str) -> float:
        """
        Algoritmo base de similitud con preprocesamiento y tokenización básica.
        """
        if not text1 or not text2:
            return 0.0
            
        # Tokenización y limpieza básica para evitar errores típicos [cite: 68, 302]
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        # Distancia de Levenshtein normalizada (Puntaje 0 a 1)
        max_len = max(len(t1), len(t2))
        if max_len == 0:
            return 1.0
            
        distance = Levenshtein.distance(t1, t2)
        similarity = 1 - (distance / max_len)
        return round(similarity, 5)
    @staticmethod
    def calculate_similarity_SequenceMatcher(text1: str, text2: str) -> float:
        """
        Algoritmo alternativo de similitud usando SequenceMatcher (difflib).
        """
        if not text1 or not text2:
            return 0.0

        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        # Similaridad basada en razón de coincidencia de secuencias
        similarity = SequenceMatcher(None, t1, t2).ratio()
        return round(similarity, 5)
    @staticmethod
    def calculate_similarity_jaccard(text1: str, text2: str) -> float:
        """
        Algoritmo alternativo de similitud usando Jaccard sobre tokens.
        """
        if not text1 or not text2:
            return 0.0

        tokens1 = set(text1.lower().strip().split())
        tokens2 = set(text2.lower().strip().split())

        if not tokens1 and not tokens2:
            return 1.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        similarity = len(intersection) / len(union)
        return round(similarity, 5)
    @staticmethod
    def calculate_similarity_cosine(text1: str, text2: str) -> float:
        """
        Algoritmo alternativo de similitud usando coseno sobre frecuencia de tokens.
        Mejora la separación entre frases con vocabulario distinto.
        """
        if not text1 or not text2:
            return 0.0

        # Remover palabras comunes para reducir ruido semántico
        stopwords = {"de", "la", "el", "los", "las", "para", "y", "o", "un", "una", "unos", "unas"}
        tokens1 = [t for t in text1.lower().strip().split() if t and t not in stopwords]
        tokens2 = [t for t in text2.lower().strip().split() if t and t not in stopwords]

        if not tokens1 and not tokens2:
            return 1.0


        c1 = Counter(tokens1)
        c2 = Counter(tokens2)

        common = set(c1) & set(c2)
        dot = sum(c1[t] * c2[t] for t in common)
        norm1 = sqrt(sum(v * v for v in c1.values()))
        norm2 = sqrt(sum(v * v for v in c2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot / (norm1 * norm2)
        return round(similarity, 5)
    @staticmethod
    def calculate_similarity(text1: str, text2: str, method: str = "levenshtein") -> float:
        """
        Selecciona el algoritmo de similitud según el método indicado.
        """
        methods = {
            "levenshtein": SimilarityService.calculate_similarity_Levenshtein,
            "sequencematcher": SimilarityService.calculate_similarity_SequenceMatcher,
            "jaccard": SimilarityService.calculate_similarity_jaccard,
            "cosine": SimilarityService.calculate_similarity_cosine,
        }
        func = methods.get(method.lower(), SimilarityService.calculate_similarity_Levenshtein)
        return func(text1, text2)
    
def test_match_existence(ids: List[int], db: Session, threshold: float = 0.5, metodo_seleccionado: str = "sequencematcher") -> Dict[str, Any]:
    """
    Función principal que evalúa la existencia de matches entre dos items.
    
    PASOS PRINCIPALES:
    1. BÚSQUEDA BIDIRECCIONAL: Consulta si existe un match previo en BD
    2. EVALUACIÓN DE ESTADO: Determina si es positivo/negativo o no existe
    3. CÁLCULO Y ACTUALIZACIÓN: Aplica lógica de similitud si es necesario
    4. PERSISTENCIA: Inserta o actualiza registros en BD
    5. RESPUESTA: Construye y retorna resultado estructurado
    
    Args:
        ids: Lista con dos IDs de items a comparar
        db: Sesión de base de datos SQLAlchemy
        threshold: Umbral de similitud para considerar un match como positivo
        metodo_seleccionado: Método de similitud a utilizar ("levenshtein", "sequencematcher", "jaccard")
    Returns:
        dict: Estructura con mensaje de validación y resultado del match
    """

    print(f"🔍 Buscando matches para IDs: {ids[0]} y {ids[1]}")

    # --- PASO 0: identificar que registros esten en la base y que sean dos diferentes ---
    if ids[0] == ids[1]:
        raise ValueError("Los IDs de items proporcionados deben ser diferentes")
    
    # identificar que registros esten en la base en la tabla items ambos ids
    items_check_query = text("""
        SELECT COUNT(DISTINCT id_item) AS cnt
        FROM items
        WHERE id_item IN (:id1, :id2)
    """)
    items_count = db.execute(items_check_query, {"id1": str(ids[0]), "id2": str(ids[1])}).scalar()
    if items_count != 2:
        raise ValueError("Uno o ambos IDs no existen en la tabla items")

    # --- PASO 1: BÚSQUEDA BIDIRECCIONAL EN TABLA MATCHES ---
    # Busca coincidencias en ambos sentidos (item1-item2 o item2-item1)
    # Esto garantiza que no importa el orden de los IDs ingresados
    check_query = text("""
        SELECT 
            id_item_1, 
            title_item_1, 
            id_item_2, 
            title_item_2,
            score, 
            status, 
            created_at, 
            updated_at
        FROM matches
        WHERE (
            (id_item_1 = :id1 AND id_item_2 = :id2)
            OR (id_item_1 = :id2 AND id_item_2 = :id1)
        )
        ORDER BY updated_at DESC
        LIMIT 1
    """)

    existing_match = db.execute(check_query, {"id1": str(ids[0]), "id2": str(ids[1])})
    result = existing_match.fetchone()

    # --- PASO 2: EVALUACIÓN Y CONSTRUCCIÓN DE RESPUESTA SEGÚN ESTADO ---
    if result:
        # ═══════════════════════════════════════════════════════════════
        # RAMA A: Match encontrado - evaluar estado (positivo/negativo)
        # ═══════════════════════════════════════════════════════════════
        
        if result.status == 'positivo':
            # SUB-PASO 2.1: MATCH POSITIVO - Retornar resultado existente
            accion_recomendada = f"""
            ✅ MATCH POSITIVO ENCONTRADO
                → Retornar resultado existente   
            Score: {result.score} | Creado: {result.created_at}
            """
            print(accion_recomendada)
            
            # SUB-PASO 2.2: Construir estructura de respuesta del match positivo
            cuerpo = {
                "id_item_1": str(result.id_item_1),
                "title_item_1": result.title_item_1,
                "id_item_2": str(result.id_item_2),
                "title_item_2": result.title_item_2,
                "score": result.score,
                "status": result.status,
                "created_at": result.created_at.isoformat() if hasattr(result.created_at, 'isoformat') else str(result.created_at),
                "updated_at": result.updated_at.isoformat() if hasattr(result.updated_at, 'isoformat') else str(result.updated_at),
            }
            print("\n📦 Respuesta construida:")
            for key, value in cuerpo.items():
                print(f"   {key}: {value}")
                
        else:  # status == 'negativo'
            # SUB-PASO 2.3: MATCH NEGATIVO - Recalcular (lógica permite actualizar)
            accion_recomendada = f"""
                ⚠️  MATCH NEGATIVO ENCONTRADO
                    → Permitir recálculo (lógica de negocio permite actualizar negativos)   
                Score: {result.score} | Creado: {result.created_at}
                """
            print(accion_recomendada)
            
            # SUB-PASO 2.3.1: Obtener datos de items desde tabla items
            item_query = text(
                """
                SELECT id_item, title 
                FROM items
                WHERE (
                    (id_item = :id1)
                    OR (id_item = :id2)
                    )
                """)   
            items = db.execute(item_query, {"id1": str(ids[0]), "id2": str(ids[1])}).fetchall()
            item1, item2 = items[0], items[1]
            
            # SUB-PASO 2.3.2: Calcular similitud usando algoritmo robusto
            score = SimilarityService.calculate_similarity(item1.title, item2.title, method=metodo_seleccionado)

            # SUB-PASO 2.3.3: Generar timestamp de actualización
            current_date = datetime.now().isoformat()

            # SUB-PASO 2.3.4: Determinar nuevo estado basado en threshold (0.85)
            status = "positivo" if score >= threshold else "negativo"

            # SUB-PASO 2.3.5: Construir estructura de respuesta con datos recalculados
            cuerpo = {
                "id_item_1": str(item1.id_item),
                "title_item_1": item1.title,
                "id_item_2": str(item2.id_item),
                "title_item_2": item2.title,
                "score": score,
                "status": status,
                "created_at": result.created_at.isoformat() if hasattr(result.created_at, 'isoformat') else str(result.created_at),
                "updated_at": current_date, 
            }

            # SUB-PASO 2.3.6: PERSISTENCIA - Actualizar registro en base de datos
            
            # 2.3.6.1: Obtener el siguiente ID disponible
            last_id_query = text("SELECT COALESCE(MAX(id), 0) as max_id FROM matches")
            last_id_result = db.execute(last_id_query).fetchone()
            new_id = last_id_result.max_id + 1
            
            # 2.3.6.2: Insertar nuevo match con datos recalculados
            insert_query = text("""
                INSERT INTO matches 
                (id, id_item_1, title_item_1, id_item_2, title_item_2, score, status, created_at, updated_at) 
                VALUES 
                (:id, :id_item_1, :title_item_1, :id_item_2, :title_item_2, :score, :status, :created_at, :updated_at)
            """)
            
            db.execute(
                insert_query,
                {
                    "id": new_id,
                    "id_item_1": cuerpo["id_item_1"],
                    "title_item_1": cuerpo["title_item_1"],
                    "id_item_2": cuerpo["id_item_2"],
                    "title_item_2": cuerpo["title_item_2"],
                    "score": cuerpo["score"],
                    "status": cuerpo["status"],
                    "created_at": cuerpo["created_at"],
                    "updated_at": cuerpo["updated_at"]
                }
            )
            db.commit()

            print("\n📦 Respuesta construida tras recalculo:")
            for key, value in cuerpo.items():
                print(f"   {key}: {value}")

    else:
        # ═══════════════════════════════════════════════════════════════
        # RAMA B: No existe match previo - Calcular y registrar nuevo
        # ═══════════════════════════════════════════════════════════════
        
        accion_recomendada = f"""
            ❌ NO SE ENCONTRÓ MATCH PREVIO
                → Proceder con cálculo de similitud y registro en BD
            """
        print(accion_recomendada)
        
        # SUB-PASO 2.4.1: Obtener datos de items desde tabla items
        item_query = text(
            """
            SELECT id_item, title 
            FROM items
            WHERE (
                (id_item = :id1)
                OR (id_item = :id2)
                )
            """)   
        items = db.execute(item_query, {"id1": str(ids[0]), "id2": str(ids[1])}).fetchall()
        item1, item2 = items[0], items[1]

        # SUB-PASO 2.4.2: Calcular similitud usando algoritmo robusto
        score = SimilarityService.calculate_similarity(item1.title, item2.title, method=metodo_seleccionado)

        # SUB-PASO 2.4.3: Generar timestamp de creación
        current_date = datetime.now().isoformat()

        # SUB-PASO 2.4.4: Determinar estado inicial basado en threshold (0.85)
        status = "positivo" if score >= threshold else "negativo"

        # SUB-PASO 2.4.5: Construir estructura de respuesta del nuevo match
        cuerpo = {
            "id_item_1": str(item1.id_item),
            "title_item_1": item1.title,
            "id_item_2": str(item2.id_item),
            "title_item_2": item2.title,
            "score": score,
            "status": status,
            "created_at": current_date,
            "updated_at": current_date, 
        }

        # SUB-PASO 2.4.6: PERSISTENCIA - Insertar nuevo match en base de datos
        
        # 2.4.6.1: Obtener el siguiente ID disponible
        last_id_query = text("SELECT COALESCE(MAX(id), 0) as max_id FROM matches")
        last_id_result = db.execute(last_id_query).fetchone()
        new_id = last_id_result.max_id + 1
        
        # 2.4.6.2: Insertar nuevo registro de match
        insert_query = text("""
            INSERT INTO matches 
            (id, id_item_1, title_item_1, id_item_2, title_item_2, score, status, created_at, updated_at) 
            VALUES 
            (:id, :id_item_1, :title_item_1, :id_item_2, :title_item_2, :score, :status, :created_at, :updated_at)
        """)
        
        db.execute(
            insert_query,
            {
                "id": new_id,
                "id_item_1": cuerpo["id_item_1"],
                "title_item_1": cuerpo["title_item_1"],
                "id_item_2": cuerpo["id_item_2"],
                "title_item_2": cuerpo["title_item_2"],
                "score": cuerpo["score"],
                "status": cuerpo["status"],
                "created_at": cuerpo["created_at"],
                "updated_at": cuerpo["updated_at"]
            }
        )
        db.commit()
        
        print(f"✅ Registro insertado exitosamente:")
        print(f"   id={new_id}, id_item_1={cuerpo['id_item_1']}, title_item_1={cuerpo['title_item_1']}")
        print(f"   id_item_2={cuerpo['id_item_2']}, title_item_2={cuerpo['title_item_2']}")
        print(f"   score={cuerpo['score']}, status={cuerpo['status']}")
        print("\n📦 Respuesta construida tras recalculo:")
        for key, value in cuerpo.items():
            print(f"   {key}: {value}")

    # --- PASO 3: RESUMEN Y LOGGING DE VALIDACIÓN ---
    print("\n" + "="*70)
    print("RESUMEN DE VALIDACIÓN:")
    print(f"  • IDs consultados: {ids}")
    print(f"  • Match encontrado: {'Sí' if result else 'No'}")
    if result:
        print(f"  • Estado del match encontrado: {result.status.upper()}")
        print(f"  • Acción recomendada: {accion_recomendada.strip()}")
    print("="*70)

    # --- PASO 4: CONSTRUCCIÓN DE RESPUESTA FINAL ESTRUCTURADA ---
    mensaje = {
        "ids_consultados": ids,
        "match_encontrado": "Sí" if result else "No",
        "estado_match_encontrado": result.status.upper() if result else "N/A",
        "accion_recomendada": accion_recomendada.strip() if result else "Proceder con cálculo de similitud y registro en BD",
    }

    resultado = {
        "mensaje": mensaje,
        "resultado": cuerpo,
    }

    return resultado



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

@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_item(item: ItemCreate, db: Session = Depends(get_db)):
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


@app.get("/tables/{table_name}/colnames", response_model=TableHeaderResponse)
async def get_table_header(table_name: str, db: Session = Depends(get_db)) -> TableHeaderResponse:
    """
    Obtiene los nombres de las columnas (cabecera) de una tabla específica.
    """
    # TODO: Implementar lógica de negocio
    # 1. Conectar a la DB.
    # 2. Usar introspección de SQLAlchemy o una consulta SQL para obtener las columnas.
    # 3. Validar que la tabla exista. Si no, HTTPException 404.
    # 4. Retornar la lista de columnas.
    print(f"Obteniendo cabecera de la tabla: {table_name}")
    
    try:
        inspector = inspect(engine)
        
        # 1. Validación de existencia
        if not inspector.has_table(table_name):
            # No se atrapará en el bloque 'except Exception' de abajo si usamos el orden correcto
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"La tabla '{table_name}' no existe en el esquema actual de la SIC."
            )

        # 2. Introspección de metadatos
        columns_metadata = inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns_metadata]

        return TableHeaderResponse(
            table_name=table_name, 
            columns=column_names
        )

    except HTTPException as http_exc:
        # Re-lanzamos errores controlados (404, 400, etc.) para que FastAPI los maneje [cite: 980]
        raise http_exc
        
    except Exception as e:
        # Solo errores no previstos (pérdida de conexión, etc.) generan un 500 [cite: 848, 913]
        # Integración con carpeta de logs de la arquitectura [cite: 603, 604]
        print(f"FALLO CRÍTICO DE INFRAESTRUCTURA: {str(e)}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar metadatos de la tabla."
        )


@app.get("/tables/{table_name}/header", response_model=List[Dict[str, Any]])
async def get_table_sample(
    table_name: str = Path(..., description="Nombre de la tabla a consultar."),
    db: Session = Depends(get_db) # Inyección automática por FastAPI [cite: 591]
):
    """
    Obtiene una muestra de 3 filas. 
    Arquitectura: MVC (Controlador)[cite: 926, 974].
    Seguridad: Ejecución en clúster privado AKS[cite: 97, 272].
    """
    try:
        # Validación vía inspección (Arquitectura de Seguridad) [cite: 88, 527]
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Tabla '{table_name}' no encontrada en el esquema."
            )

        # Consulta segura con SQLAlchemy Core [cite: 391, 650]
        query = text(f"SELECT * FROM {table_name} LIMIT 3")
        
        # 'db' debe ser una instancia de sqlalchemy.orm.Session
        result = db.execute(query)
        
        # Mapeo a diccionario para respuesta JSON [cite: 973, 987]
        return [dict(row._mapping) for row in result]

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        # Registro detallado en carpeta logs/ [cite: 91, 604]
        print(f"ERROR DE INFRAESTRUCTURA DB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fallo en la conexión con la base de datos institucional."
        )

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

@app.post("/matches/compare-by-ids")
async def compare_items_by_ids(id_a: int, id_b: int, db: Session = Depends(get_db)):
    """
    Compara dos items existentes por sus IDs y utiliza test_match_existence para evaluar el match.
    
    - Si ya existe un match **POSITIVO** entre los IDs, no se hace nada.
    - Si el match existe pero con otro estado, se recalcula y actualiza.
    - Si no existe, se crea uno nuevo.
    """
    try:
        resultado = test_match_existence([id_a, id_b], db, threshold=0.85, metodo_seleccionado="sequencematcher")
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
