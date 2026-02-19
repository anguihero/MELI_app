import os
from datetime import datetime
from enum import Enum
from math import sqrt
from collections import Counter
from typing import List, Dict, Any, Optional

# --- 1. Framework Core & HTTP ---
from fastapi import FastAPI, HTTPException, Query, status, Path, Depends

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
    id: int = Field(..., description="Identificador único del producto.", example=123456)
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
    id_a: int = Field(..., description="ID del primer item.", example=123456)
    id_b: int = Field(..., description="ID del segundo item.", example=654321)

class MatchResponse(BaseModel):
    """Schema para la respuesta de un match."""
    id: int = Field(..., description="ID único del match.", example=101)
    id_item_1: str = Field(..., description="ID del primer producto.", example="123456")
    title_item_1: str = Field(..., description="Título del primer producto.", example="Celular Samsung Galaxy S23")
    id_item_2: str = Field(..., description="ID del segundo producto.", example="654321")
    title_item_2: str = Field(..., description="Título del segundo producto.", example="Samsung S23 128GB")
    score: float = Field(..., description="Puntuación de similitud del match.", example=0.95)
    status: StatusEnum = Field(..., description="Estado del match.", example=StatusEnum.positivo)

class HealthResponse(BaseModel):
    """Schema para la respuesta del health check."""
    status: str = "ok"
    message: Optional[str] = "Conectividad con la base de datos verificada exitosamente"

# Definición del modelo de respuesta
class TableHeaderResponse(BaseModel):
    table_name: str
    columns: list[str]

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

def insert_item(db: Session, id_item: int, title: str):
    """
    Inserta un nuevo registro en la tabla 'items'.
    
    Args:
        db: Sesión de SQLAlchemy para ejecutar queries
        id_item: ID único del item a insertar
        title: Título descriptivo del item
    
    Returns:
        str: Mensaje indicando el resultado de la operación
    
    Raises:
        SQLAlchemyError: Si falla la inserción en base de datos
    """
    
    # verificar si ya existe el id_item y en caso de que si, no insertar y retornar mensaje de error
    check_query = text("SELECT id FROM items WHERE id_item = :id_item")
    existing_item = db.execute(check_query, {"id_item": str(id_item)}).fetchone()
    if existing_item:
        mensaje = f"❌ Item ya existe: id_item={id_item}, title='{title}' \n No se insertó el registro para evitar duplicados."
        print(mensaje)
        return mensaje
    
    # 2.4.6.1: Obtener el siguiente ID disponible
    last_id_query = text("SELECT COALESCE(MAX(id), 0) as max_id FROM matches")
    last_id_result = db.execute(last_id_query).fetchone()
    new_id = last_id_result.max_id + 1
    
    # 2. GENERAR TIMESTAMP ACTUAL
    current_timestamp = datetime.now().isoformat()
    
    # 3. INSERTAR REGISTRO EN TABLA ITEMS
    insert_query = text("""
        INSERT INTO items 
        (id, id_item, title, created_at, updated_at) 
        VALUES 
        (:id, :id_item, :title, :created_at, :updated_at)
    """)
    
    db.execute(
        insert_query,
        {
            "id": new_id,
            "id_item": str(id_item),
            "title": title,
            "created_at": current_timestamp,
            "updated_at": current_timestamp
        }
    )
    
    # 4. CONFIRMAR TRANSACCIÓN
    db.commit()
    
    mensaje = f"✅ Item insertado exitosamente: id={new_id}, id_item={id_item}, title='{title}'"
    print(mensaje)
    return mensaje

# --- Aplicación FastAPI ---

app = FastAPI(
    title="MELI Challenge API",
    description=(
        "API para el Desafío de Desarrollo Op 2 - AA&ML de MercadoLibre.\n\n"
        "**Desarrollador:** https://github.com/anguihero & https://www.linkedin.com/in/amms1989/ \n\n"
        "**Propósito:** Demostrar suficiencia técnica en desarrollo de microservicios, "
        "manejo de datos y diseño de APIs RESTful.\n\n"
        "## Descripción\n"
        "API diseñada para resolver desafíos técnicos de MercadoLibre en el contexto de "
        "Aprendizaje Automático y Analítica Avanzada. Proporciona endpoints para gestión "
        "de items, comparación de similitudes y operaciones con matches.\n\n"
        "## Características Principales\n\n"
        "### 1. Gestión de Items\n"
        "- Crear o actualizar registros de productos\n"
        "- Validación de unicidad en títulos\n\n"
        "### 2. Comparación de Similitudes\n"
        "- Múltiples algoritmos: Levenshtein, SequenceMatcher, Jaccard, Cosine\n"
        "- Comparación de textos arbitrarios\n"
        "- Comparación de productos por IDs\n\n"
        "### 3. Operaciones sobre Matches\n"
        "- Recuperación de información de matches\n"
        "- Respaldo y reseteo de la tabla de matches\n\n"
        "### 4. Salud y Metadatos\n"
        "- Verificación de conectividad con base de datos\n"
        "- Obtención de esquemas de tablas\n"
        "- Muestras de datos de tablas específicas\n\n"
        "## Tecnologías\n"
        "- **Framework:** FastAPI\n"
        "- **Validación:** Pydantic\n"
        "- **Base de datos:** PostgreSQL con SQLAlchemy\n"
        "- **Algoritmos NLP:** Levenshtein, difflib, similitud de coseno\n"
    ),
    version="1.0.0",
)

# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Verifica la conectividad con la base de datos.
    
    Retorna un status "ok" si la conexión es exitosa.
    En caso de error, retorna un HTTPException con status 503 (Service Unavailable).
    """
    try:
        # Intentar hacer una consulta simple a la BD
        db.execute(text("SELECT 1"))
        # Retornar respuesta exitosa con información de lo evaluado
        return HealthResponse(
            status="ok",
            message="Conectividad con la base de datos verificada exitosamente"
        )
    except Exception as e:
        # Si falla, lanzar HTTPException 503 (Service Unavailable)
        print(f"❌ Error de conectividad con la BD: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible"
        )

@app.post("/matches/testing-text", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def test_match_from_texts(
    match_data: MatchCreate, 
    UMBRAL: float = 0.5,
    method: str = "levenshtein"
):
    """
    Calcula la similitud entre dos textos sin consultar la API de Mercado Libre ni persistir en base de datos.

    Esta función de prueba permite evaluar diferentes algoritmos de similitud entre dos textos arbitrarios.
    Genera IDs ficticios para simular items, calcula el score de similitud usando el método especificado,
    y retorna un objeto MatchResponse con el resultado del análisis.

    Endpoint: POST /matches/testing-text

    Method: Asíncrono
        match_data (MatchCreate): Objeto que contiene los dos textos a comparar (text_1 y text_2).
        UMBRAL (float, optional): Umbral de similitud para determinar si el match es positivo o negativo.
            Si score >= UMBRAL, el estado será "positivo", caso contrario "negativo". Por defecto: 0.5.
        method (str, optional): Método de similitud a utilizar. Opciones disponibles:
            - "levenshtein": Distancia de Levenshtein normalizada
            - "sequencematcher": SequenceMatcher de Python
            - "jaccard": Similitud de Jaccard
            - "cosine": Similitud de coseno
            Por defecto: "levenshtein".

    Returns:
        MatchResponse: Objeto con los siguientes campos:
            - id: ID único generado para el match
            - id_item_1: ID ficticio del primer item
            - title_item_1: Texto 1 proporcionado
            - id_item_2: ID ficticio del segundo item
            - title_item_2: Texto 2 proporcionado
            - score: Puntuación de similitud calculada (0.0 - 1.0)
            - status: Estado del match ("positivo" o "negativo")

    Raises:
        HTTPException: 
            - 500 Internal Server Error: Si ocurre un error durante el cálculo de similitud.

    Example:
        ```python
        match_data = MatchCreate(text_1="Smartphone Samsung", text_2="Celular Samsung")
        result = await test_match_from_texts(match_data, UMBRAL=0.7, method="cosine")
        # result.score -> 0.7
        # result.status -> "positivo"
        ```

    Note:
        - Esta función NO realiza llamadas a la API de Mercado Libre.
        - Los resultados NO se persisten en la base de datos.
        - Los IDs generados son ficticios y únicos basados en timestamp.
        - Útil para testing y comparación de algoritmos de similitud.
    """
    try:
        # Generar IDs ficticios para los items
        item1_id = f"MLA_TEXT_{int(datetime.now().timestamp())}_1"
        item2_id = f"MLA_TEXT_{int(datetime.now().timestamp())}_2"
        
        # Calcular similitud usando algoritmo seleccionado
        score = SimilarityService.calculate_similarity(
            match_data.text_1, 
            match_data.text_2, 
            method=method
        )
        
        # Generar timestamp actual
        current_date = datetime.now().isoformat()
        
        # Determinar estado basado en threshold (0.85)
        match_status = "positivo" if score >= UMBRAL else "negativo"
        
        # Generar ID ficticio para el match
        new_match_id = int(datetime.now().timestamp() * 1000) % 999999
        
        return MatchResponse(
            id=new_match_id,
            id_item_1=item1_id,
            title_item_1=match_data.text_1,
            id_item_2=item2_id,
            title_item_2=match_data.text_2,
            score=score,
            status=match_status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular similitud: {str(e)}"
        )


@app.post("/matches/compare-by-ids")
async def compare_items_by_ids(id_a: int, id_b: int, UMBRAL: float = 0.5, db: Session = Depends(get_db)):
    """
    Compara dos items por sus IDs y determina si son duplicados.
    Este endpoint permite comparar dos items existentes en la base de datos utilizando
    sus IDs. Evalúa si existe un match entre ellos usando el método SequenceMatcher
    con un umbral de similitud seleccionado.

    Comportamiento:
        - Si ya existe un match POSITIVO entre los IDs, retorna el resultado existente
        - Si el match existe con otro estado, lo recalcula y actualiza
        - Si no existe match, crea uno nuevo

    Endpoint:
        POST /matches/compare-by-ids (o similar) - verifica con la configuración de rutas

    Args:
        id_a (int): ID del primer item a comparar
        id_b (int): ID del segundo item a comparar
        db (Session, optional): Sesión de base de datos inyectada por dependencia

    Returns:
        dict: Resultado del análisis de match con información de similitud y estado

    Raises:
        HTTPException(400): Si los IDs son inválidos o no existen en la base de datos
        HTTPException(500): Si ocurre un error interno durante el procesamiento

    Example:
        ```
        POST /matches/compare-by-ids?id_a=123&id_b=456

        Response:
        {
            "mensaje": {
                "ids_consultados": [
                123456789,
                123456
                ],
                "match_encontrado": "Sí",
                "estado_match_encontrado": "POSITIVO",
                "accion_recomendada": "✅ MATCH POSITIVO ENCONTRADO\n                → Retornar resultado existente   \n            Score: 1.0 | Creado: 2026-02-18 21:55:14.036671+00:00"
            },
            "resultado": {
                "id_item_1": "123456",
                "title_item_1": "Celular Samsung Galaxy S23",
                "id_item_2": "123456789",
                "title_item_2": "Celular Samsung Galaxy S23",
                "score": 1,
                "status": "positivo",
                "created_at": "2026-02-18T21:55:14.036671+00:00",
                "updated_at": "2026-02-18T21:55:14.036671+00:00"
            }
            }
        ```
    """
    try:
        resultado = test_match_existence([id_a, id_b], db, threshold=UMBRAL, metodo_seleccionado="sequencematcher")
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/tables/{table_name}/colnames", response_model=TableHeaderResponse)
async def get_table_header(table_name: str, db: Session = Depends(get_db)) -> TableHeaderResponse:
    """
    Obtiene los nombres de las columnas (cabecera) de una tabla específica de la base de datos.

    Este endpoint realiza introspección en la base de datos para extraer los metadatos
    de una tabla y retornar la lista de nombres de sus columnas.

    Args:
        table_name (str): Nombre de la tabla de la cual se desea obtener la cabecera.
        db (Session, optional): Sesión de base de datos inyectada mediante Depends(get_db).

    Returns:
        TableHeaderResponse: Objeto que contiene el nombre de la tabla y la lista de columnas.
            - table_name (str): Nombre de la tabla consultada.
            - columns (List[str]): Lista con los nombres de todas las columnas de la tabla.

    Raises:
        HTTPException: 
            - 404 NOT_FOUND: Si la tabla especificada no existe en el esquema de la base de datos.
            - 500 INTERNAL_SERVER_ERROR: Si ocurre un error inesperado durante la introspección
              o consulta de metadatos (ej: pérdida de conexión, error de base de datos).

    Endpoint:
        GET /tables/{table_name}/header


    Process:
        1. Conecta al motor de base de datos y crea un inspector.
        2. Valida la existencia de la tabla en el esquema.
        3. Realiza introspección para obtener los metadatos de las columnas.
        4. Extrae y retorna los nombres de las columnas.
    """

    print(f"Obteniendo cabecera de la tabla: {table_name}")
    
    try:
        inspector = inspect(engine)
        
        # 1. Validación de existencia
        if not inspector.has_table(table_name):
            # No se atrapará en el bloque 'except Exception' de abajo si usamos el orden correcto
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"La tabla '{table_name}' no existe en el esquema actual"
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
    rows: int = Query(3, description="Número de filas a retornar como muestra.", ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Endpoint GET para obtener una muestra de registros de una tabla específica.

    Este endpoint recupera un número limitado de filas de una tabla de base de datos,
    ordenadas por fecha de modificación descendente (si existe la columna 'updated_at').

    **Endpoint:** GET /tables/{table_name}/sample

    **Parámetros:**
        - table_name (str): Nombre de la tabla a consultar (parámetro de ruta).
        - rows (int): Número de filas a retornar (query parameter, rango: 1-100, default: 3).
        - db (Session): Sesión de base de datos inyectada automáticamente.

    **Respuestas:**
        - 200 OK: Lista de diccionarios con los registros de la tabla.
        - 404 NOT FOUND: La tabla especificada no existe en el esquema.
        - 500 INTERNAL SERVER ERROR: Error de conexión o ejecución en la base de datos.

    **Retorna:**
        List[Dict]: Lista de diccionarios donde cada elemento representa una fila de la tabla,
                    con las claves correspondientes a los nombres de columnas.

    **Comportamiento:**
        1. Valida la existencia de la tabla mediante inspección del esquema.
        2. Verifica si existe la columna 'updated_at' para aplicar ordenamiento descendente.
        3. Ejecuta consulta parametrizada para prevenir inyección SQL.
        4. Convierte los resultados a formato JSON serializable.

    **Arquitectura:**
        - Patrón: MVC (Controlador)
        - Seguridad: Ejecución en clúster privado AKS, consultas parametrizadas.
        - Validación: Inspección de esquema antes de ejecutar consultas dinámicas.

    **Ejemplo de uso:**
        GET /tables/usuarios/sample?rows=5

    **Ejemplo de respuesta:**
        [
            {"id": 123, "nombre": "Juan", "updated_at": "2024-01-15T10:30:00"},
            {"id": 122, "nombre": "María", "updated_at": "2024-01-14T15:20:00"}
        ]
    """
    try:
        # Validación vía inspección (Arquitectura de Seguridad)
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Tabla '{table_name}' no encontrada en el esquema."
            )

        # Verificar si la tabla tiene columna 'updated_at' para ordenar
        columns = inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]
        
        # Construir query con ORDER BY dinámico
        if 'updated_at' in column_names:
            query = text(f"SELECT * FROM {table_name} ORDER BY updated_at DESC LIMIT :limit")
        else:
            query = text(f"SELECT * FROM {table_name} LIMIT :limit")
        
        # Ejecutar consulta con parámetro seguro
        result = db.execute(query, {"limit": rows})
        
        # Mapeo a diccionario para respuesta JSON
        return [dict(row._mapping) for row in result]

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"ERROR DE INFRAESTRUCTURA DB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fallo en la conexión con la base de datos institucional."
        )


@app.post("/tables/add-items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_item(item: ItemCreate, db: Session = Depends(get_db)):
    """
    Endpoint para crear o actualizar un ítem en la base de datos.
    Este endpoint recibe los datos de un ítem y realiza las siguientes operaciones:
        - Valida que el ID sea un número entero válido
        - Verifica que el título sea único en la base de datos
        - Inserta un nuevo registro o actualiza uno existente según el ID proporcionado

    Args:
        item (ItemCreate): Objeto que contiene los datos del ítem a crear/actualizar.
            - id (str): Identificador único del ítem (será convertido a entero)
            - title (str): Título del ítem (debe ser único)
        db (Session, optional): Sesión de base de datos inyectada por dependencia.

    Returns:
        ItemResponse: Objeto con la información del ítem procesado y un mensaje de confirmación.
            - id (str): ID del ítem procesado
            - title (str): Título del ítem procesado
            - message (str): Mensaje indicando si fue creado o actualizado

    Raises:
        HTTPException 400: Si el ID proporcionado no es un número entero válido.
        HTTPException 500: Si ocurre un error durante la operación de base de datos.

    Example:
        ```json
        POST /items
        {
            "id": "123",
            "title": "Ejemplo de producto"
        }
        ```
    """
    try:
        # Convertir el id de string a integer
        item_id = int(item.id)
        
        # Usar la función insert_item para insertar/validar el item
        mensaje = insert_item(db, item_id, item.title)
        
        return ItemResponse(id=item.id, title=item.title, message=mensaje)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID debe ser un número entero válido"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al insertar item: {str(e)}"
        )

# @app.post("/tables/matches/backup-and-reset", response_model=BackupResponse)
# async def backup_and_reset_table_matches(db: Session = Depends(get_db)):

#     """
#     Realiza un backup completo de la tabla 'matches' y la resetea.

#     Esta función de endpoint ejecuta las siguientes operaciones en orden:

#     1. Cuenta los registros existentes en la tabla 'matches'
#     2. Copia todos los registros de 'matches' a 'matches_backup'
#     3. Elimina todos los registros de la tabla 'matches'
#     4. Confirma la transacción si todo es exitoso

#     Endpoint: POST /backup-and-reset-matches
#     Args:
#         db (Session, optional): Sesión de base de datos inyectada mediante Depends(get_db).

#     Returns:
#         BackupResponse: Objeto con el mensaje de éxito y la cantidad de registros movidos.
#             - message (str): Mensaje descriptivo del resultado de la operación
#             - records_moved (int): Número de registros transferidos a matches_backup

#     Raises:
#         HTTPException: 
#             - status_code 500: Error interno durante el proceso de backup o reseteo.
#               Incluye el detalle del error en el mensaje.

#     Notes:
#         - Si la tabla 'matches' está vacía, retorna inmediatamente sin realizar operaciones
#         - Utiliza transacciones para garantizar la consistencia de datos
#         - En caso de error, ejecuta rollback automático
#         - Los estados de 'status' se convierten al tipo enum 'match_backup_status_enum'
#     """
#     try:
#         # 1. Contar registros antes del backup
#         count_query = text("SELECT COUNT(*) as total FROM matches")
#         count_result = db.execute(count_query).fetchone()
#         records_to_backup = count_result.total if count_result else 0
        
#         if records_to_backup == 0:
#             return BackupResponse(
#                 message="✅ No hay registros para hacer backup. La tabla 'matches' está vacía.",
#                 records_moved=0
#             )
        
#         # 2. Copiar todos los datos de 'matches' a 'matches_backup'
#         copy_query = text("""
#             INSERT INTO matches_backup 
#             (id, id_item_1, title_item_1, id_item_2, title_item_2, score, status, created_at, updated_at)
#             SELECT id, id_item_1, title_item_1, id_item_2, title_item_2, score, status::text::match_backup_status_enum, created_at, updated_at 
#             FROM matches
#         """)
#         db.execute(copy_query)
        
#         # 3. Eliminar todos los registros de 'matches'
#         delete_query = text("DELETE FROM matches")
#         db.execute(delete_query)
        
#         # 4. Hacer commit de la transacción
#         db.commit()
        
#         print(f"✅ Backup completado exitosamente: {records_to_backup} registros movidos a 'matches_backup'")
#         print(f"✅ Tabla 'matches' vaciada correctamente")
        
#         return BackupResponse(
#             message=f"✅ Backup completado y tabla 'matches' reseteada exitosamente. {records_to_backup} registros fueron movidos a 'matches_backup'.",
#             records_moved=records_to_backup
#         )
        
#     except Exception as e:
#         db.rollback()
#         print(f"❌ Error durante el backup y reseteo: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error al realizar backup y reseteo: {str(e)}"
#         )