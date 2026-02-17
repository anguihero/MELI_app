# Plan de Trabajo: Meli Matches Challenge

## Etapa 1: Revisión de requerimiento y solicitud
- [ x ] Entendimiento del requerimiento (Challenge Meli Matches.pdf).
- [ x ] Documentar Historias tecnicas en el plan de trabajo.

## Etapa 2: Definición y Skeleton
- [ x ] **Configuración del Entorno**: Establecer el entorno de desarrollo con Python 3.12 y `pip` para la gestión de dependencias.
    - [ x ] **Criterios de Aceptación**:
        - [ x ] El archivo `requirements.txt` está creado y lista todas las dependencias necesarias.
        - [ x ] El entorno virtual se puede crear y activar sin errores.
- [ x ] **Diseño de Base de Datos**: Documentar el schema de la base de datos, definiendo las tablas y relaciones utilizando modelos de SQLAlchemy.
    - [ x ] **Criterios de Aceptación**:
        - [ x ] Se definen los modelos para las tablas `items`, `matches` y `matches_backup`.
        - [ x ] La tabla `items` almacena los textos a comparar (`id`, `title`).
        - [ x ] La tabla `matches` guarda el resultado de cada comparación (`id_item_1`, `title_item_1`, `id_item_2`, `title_item_2`,`score`, `status`, `created_at`, `updated_at`).
        - [ x ] La tabla `matches_backup` sirve como archivo histórico de los matches procesados (`id_item_1`, `title_item_1`, `id_item_2`, `title_item_2`,`score`, `status`, `created_at`, `updated_at`) adicionando una columna `restored_at` indicando en el momento en el que se realiza el backup.
        - [ x ] El schema se documenta claramente en un archivo markdown y/o mediante un diagrama.
- [ ] **Diseño de Arquitectura**: Elaborar un documento que detalle la arquitectura de 3 capas (API, Servicios, Persistencia) de la solución.
    - [ ] **Criterios de Aceptación**:
        - [ ] El documento explica claramente las responsabilidades de cada capa.
        - [ ] Se define la estructura de directorios del proyecto.


## Etapa 3: Implementación de la base de datos
- [ x ] **Implementación de la Base de Datos**: Crear el script de inicialización de la base de datos y configurar la conexión desde la aplicación.
    - [ x ] **Criterios de Aceptación**:
        - [ x ] Se implementa la conexión a la base de datos utilizando SQLAlchemy.
        - [ x ] Un script o comando permite crear todas las tablas a partir de los modelos definidos.
        - [ x ] La configuración de la conexión (URL de la base de datos) se gestiona a través de variables de entorno.

## Etapa 4: Lógica de Negocio y API

- [ ] **Desarrollo de Endpoints**: Implementar los endpoints en FastAPI, incluyendo la validación de datos con Pydantic y la documentación automática con Swagger UI.
    - [ ] **Criterios de Aceptación**:
        - [ ] La interfaz de Swagger UI (`/docs`) está disponible y permite probar todos los endpoints.
        - [ ] `POST /matches`: Acepta dos textos, calcula el match, lo persiste y devuelve el resultado.
        - [ ] `POST /matches/compare-by-ids`: Acepta dos IDs de items, los recupera de la tabla `items`, los compara y guarda/actualiza el resultado en la tabla `matches`. Si el match ya existe con estado `POSITIVO`, no se realiza ninguna acción. Si existe con otro estado, se recalcula y se actualizan los campos `score`, `status` y `updated_at`.
        - [ ] `GET /matches/{id}`: Recupera y devuelve un match existente por su ID.
        - [ ] `POST /items`: Permite agregar o corregir registros en la tabla `items`.
        - [ ] `GET /health`: Endpoint de salud que verifica la conectividad con los servicios clave (ej. base de datos).
        - [ ] `GET /tables/{table_name}/header`: Devuelve los nombres de las columnas de la tabla especificada.
        - [ ] `POST /matches/backup-and-reset`: Copia todos los registros de `matches` a `matches_backup` y luego elimina todos los registros de la tabla `matches`.
        - [ ] Las solicitudes con datos inválidos devuelven un error 422.
- [ ] **Implementación del Servicio de Comparación**: Desarrollar el servicio que contiene el algoritmo de similitud de texto base.
    - [ ] **Criterios de Aceptación**:
        - [ ] El servicio implementa una función que recibe dos textos y devuelve un puntaje de similitud entre 0 y 1.
        - [ ] El algoritmo de comparación (ej. Levenshtein, Jaccard) está encapsulado en esta capa.
- [ ] **Implementación de Lógica de Estados**: Codificar la lógica de negocio para manejar los estados `POSITIVO` y `NEGATIVO`, incluyendo la regla de no re-generación para matches positivos.
    - [ ] **Criterios de Aceptación**:
        - [ ] Un match con resultado >= 0.85 se marca como `POSITIVO`.
        - [ ] Un match con resultado < 0.85 se marca como `NEGATIVO`.
        - [ ] Si se solicita un `POST /matches` con textos que ya tienen un resultado `POSITIVO`, se debe devolver el resultado existente sin recalcular.
- [ ] **Configuración de Contenerización**: Crear los archivos `Dockerfile` y `docker-compose.yml` iniciales para la aplicación.
    - [ ] **Criterios de Aceptación**:
        - [ ] El comando `docker-compose up` levanta la aplicación y la base de datos.
        - [ ] La aplicación es accesible desde el host.

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
- [ ] **Optimización de Docker**: Refinar el `Dockerfile` utilizando un multi-stage build para reducir el tamaño de la imagen final.
    - [ ] **Criterios de Aceptación**:
        - [ ] El `Dockerfile` utiliza una imagen base ligera para la etapa final.
        - [ ] El tamaño de la imagen de producción es significativamente menor que la imagen de desarrollo.
- [ ] **Preparación del Repositorio**: Limpiar y organizar el repositorio de GitHub para la entrega final.
    - [ ] **Criterios de Aceptación**:
        - [ ] El historial de commits es claro y descriptivo.
        - [ ] Se eliminan archivos innecesarios o temporales.
- [ ] **(Bonus) CI/CD**: Configurar un pipeline básico de Integración Continua y Despliegue Continuo con GitHub Actions.
    - [ ] **Criterios de Aceptación**:
        - [ ] Cada push a la rama principal dispara la ejecución de las pruebas.
        - [ ] El pipeline construye la imagen Docker y la sube a un registro (ej. Docker Hub, GHCR).
