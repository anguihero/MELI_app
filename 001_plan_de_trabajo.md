# Plan de Trabajo: Meli Matches Challenge

## Etapa 1: Revisión de requerimiento y solicitud
- [x] Entendimiento del requerimiento (Challenge Meli Matches.pdf).
- [x] Documentar Historias tecnicas en el plan de trabajo.

## Etapa 2: Definición y Skeleton
- [x] **Configuración del Entorno**: Establecer el entorno de desarrollo con Python 3.12 y `pip` para la gestión de dependencias.
    - [x] **Criterios de Aceptación**:
        - [x] El archivo `requirements.txt` está creado y lista todas las dependencias necesarias.
        - [x] El entorno virtual se puede crear y activar sin errores.
- [x] **Diseño de Base de Datos**: Documentar el schema de la base de datos, definiendo las tablas y relaciones utilizando modelos de SQLAlchemy.
    - [x] **Criterios de Aceptación**:
        - [x] Se definen los modelos para las tablas `items`, `matches` y `matches_backup`.
        - [x] La tabla `items` almacena los textos a comparar (`id`, `title`).
        - [x] La tabla `matches` guarda el resultado de cada comparación (`id_item_1`, `title_item_1`, `id_item_2`, `title_item_2`,`score`, `status`, `created_at`, `updated_at`).
        - [x] La tabla `matches_backup` sirve como archivo histórico de los matches procesados (`id_item_1`, `title_item_1`, `id_item_2`, `title_item_2`,`score`, `status`, `created_at`, `updated_at`) adicionando una columna `restored_at` indicando en el momento en el que se realiza el backup.
        - [x] El schema se documenta claramente en un archivo markdown y/o mediante un diagrama.
- [x] **Diseño de Arquitectura**: Elaborar un documento que detalle la arquitectura de 3 capas (API, Servicios, Persistencia) de la solución.
    - [x] **Criterios de Aceptación**:
        - [x] El documento explica claramente las responsabilidades de cada capa.
        - [x] Se define la estructura de directorios del proyecto.


## Etapa 3: Implementación de la base de datos
- [x] **Implementación de la Base de Datos**: Crear el script de inicialización de la base de datos y configurar la conexión desde la aplicación.
    - [x] **Criterios de Aceptación**:
        - [x] Se implementa la conexión a la base de datos utilizando SQLAlchemy.
        - [x] Un script o comando permite crear todas las tablas a partir de los modelos definidos.
        - [x] La configuración de la conexión (URL de la base de datos) se gestiona a través de variables de entorno.

## Etapa 4: Lógica de Negocio y API

- [x] **Desarrollo de Endpoints**: Implementar los endpoints en FastAPI, incluyendo la validación de datos con Pydantic y la documentación automática con Swagger UI.
    - [x] **Criterios de Aceptación**:
        - [x] La interfaz de Swagger UI (`/docs`) está disponible y permite probar todos los endpoints.
        - [x] `GET /health`: Endpoint de salud (Health Check).
        - [x] `POST /matches/testing-text`: Acepta dos textos (Test Match From Texts).
        - [x] `POST /matches/compare-by-ids`: Acepta dos IDs de items (Compare Items By Ids).
        - [x] `GET /tables/{table_name}/colnames`: Devuelve los nombres de las columnas de la tabla especificada (Get Table Header).
        - [x] `GET /tables/{table_name}/header`: Devuelve una muestra de la tabla seleccionada (Get Table Sample).
        - [x] `POST /tables/add-items`: Permite agregar o actualizar registros en la tabla `items` (Create Or Update Item).
        - [x] `POST /tables/matches/backup-and-reset`: Copia todos los registros de `matches` a `matches_backup` y luego elimina todos los registros de la tabla `matches` (Backup And Reset Table Matches).
- [x] **Implementación del Servicio de Comparación**: Desarrollar el servicio que contiene el algoritmo de similitud de texto base.
    - [x] **Criterios de Aceptación**:
        - [x] El servicio implementa una función que recibe dos textos y devuelve un puntaje de similitud entre 0 y 1.
        - [x] El algoritmo de comparación (ej. Levenshtein, Jaccard) está encapsulado en esta capa.
- [x] **Implementación de Lógica de Estados**: Codificar la lógica de negocio para manejar los estados `POSITIVO` y `NEGATIVO`, incluyendo la regla de no re-generación para matches positivos.
    - [x] **Criterios de Aceptación**:
        - [x] Un match con resultado >= UMBRAL se marca como `POSITIVO`.
        - [x] Un match con resultado < UMBRAL se marca como `NEGATIVO`.
        - [x] Si se solicita un `POST /matches` con textos que ya tienen un resultado `POSITIVO`, se debe devolver el resultado que ejemplifica como funciona el algoritmo.
        - [x] Si se solicita un `POST /matches/compare-by-ids` con dos ids diferente que ya tienen un resultado `POSITIVO`, se debe devolver el resultado existente sin recalcular.
- [x] **Configuración de Contenerización**: Crear los archivos `Dockerfile` y `docker-compose.yml` iniciales para la aplicación.
    - [x] **Criterios de Aceptación**:
        - [x] El comando `docker-compose up` levanta la aplicación y la base de datos.
        - [x] La aplicación es accesible desde el host.

## Etapa 5: Calidad y Documentación
- [ ] **Pruebas Unitarias**: Escribir pruebas unitarias para la capa de servicios y la lógica de negocio utilizando `pytest`.
    - [ ] **Criterios de Aceptación**:
        - [ ] La cobertura de pruebas para la capa de servicios es superior al 80%.
        - [ ] Se prueban casos borde para el algoritmo de similitud.
- [ ] **Pruebas de Integración**: Desarrollar pruebas de integración para los endpoints de la API utilizando `pytest` y `httpx`.
    - [ ] **Criterios de Aceptación**:
        - [ ] Se prueba el flujo completo de creación y consulta de un match.
        - [ ] Se validan los códigos de estado y las respuestas de la API para casos exitosos y de error.
- [ ] **Configuración de Logging**: Implementar un sistema de logs para registrar eventos importantes y errores de la aplicación.
    - [ ] **Criterios de Aceptación**:
        - [ ] Las solicitudes a la API y los errores internos se registran en la salida estándar o en un archivo.
        - [ ] Los logs incluyen información útil como timestamp, nivel de severidad y mensaje.
- [ ] **Documentación Técnica**: Redactar un `README.md` completo con instrucciones de instalación, configuración y uso de la API.
    - [ ] **Criterios de Aceptación**:
        - [ ] El `README.md` incluye cómo levantar el proyecto con Docker.
        - [ ] Se documentan los endpoints de la API con ejemplos de `curl`.

## Etapa 6: Despliegue y Entrega
- [x] **Optimización de Docker**: Refinar el `Dockerfile` utilizando un multi-stage build para reducir el tamaño de la imagen final.
    - [x] **Criterios de Aceptación**:
        - [x] El `Dockerfile` utiliza una imagen base ligera para la etapa final.
- [x] **Preparación del Repositorio**: Limpiar y organizar el repositorio de GitHub para la entrega final.
    - [x] **Criterios de Aceptación**:
        - [x] Se eliminan archivos innecesarios o temporales.
