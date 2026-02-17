
## Objetivos del Proyecto

### Principales (MVP)
- **API Funcional**: Exponer endpoints para crear y consultar matches de productos.
- **Lógica de Similitud**: Implementar un algoritmo base para comparar la similitud entre títulos de productos.
- **Persistencia de Datos**: Almacenar los resultados de los matches (ID_A, ID_B, score, status) en una base de datos SQLite.
- **Manejo de Estados**: Implementar la lógica de negocio para los estados `POSITIVO` y `NEGATIVO`, respetando las reglas de re-generación.
- **Contenerización**: Entregar la aplicación como una imagen Docker funcional.

### Secundarios (Bonus)
- **Optimización del Algoritmo**: Investigar y aplicar algoritmos de similitud de texto más avanzados (e.g., Jaro-Winkler, TF-IDF).
- **Pruebas de Integración**: Añadir pruebas que validen la interacción completa entre la API y la base de datos.
- **CI/CD Pipeline**: Configurar un flujo de integración y despliegue continuo básico con GitHub Actions.


## Arquitectura Propuesta

La solución se basará en una arquitectura de 3 capas para desacoplar responsabilidades:

1.  **Capa de API (FastAPI)**: Responsable de la gestión de peticiones HTTP, validación de datos de entrada (Pydantic) y la exposición de la documentación OpenAPI (Swagger).
2.  **Capa de Servicios (Lógica de Negocio)**: Orquesta la lógica de la aplicación. Coordina la obtención de datos, invoca el motor de similitud y aplica las reglas de negocio para determinar el estado de un match.
3.  **Capa de Persistencia (SQLAlchemy)**: Abstrae el acceso a la base de datos. Define los modelos de datos y gestiona las operaciones CRUD sobre la base de datos SQLite.

## Definición de "Done" (Criterios de Aceptación)

### `POST /matches`
- **Dado** un par de IDs de producto (ID_A, ID_B).
- **Cuando** se envía una solicitud POST.
- **Entonces** el sistema debe:
    1. Validar que el par no exista con estado `POSITIVO`. Si existe, retornar el match existente sin re-calcular.
    2. Si el par existe con estado `NEGATIVO` o no existe, calcular la similitud de los títulos.
    3. Actualizar (si era `NEGATIVO`) o crear el registro en la base de datos con el nuevo score y estado.
    4. Retornar el objeto del match con su ID, score y estado (`POSITIVO` o `NEGATIVO`).

### `GET /matches/{match_id}`
- **Dado** un ID de match válido.
- **Cuando** se envía una solicitud GET.
- **Entonces** el sistema debe retornar el objeto del match correspondiente desde la base de datos.
- **Y** si el ID no existe, retornar un error `404 Not Found`.

## Riesgos Técnicos
- **Falsos Positivos/Negativos**: El algoritmo de similitud de títulos puede generar resultados incorrectos (e.g., "iPhone 13 Pro" vs "Funda iPhone 13 Pro"). Se requiere un umbral de similitud bien calibrado.
- **Escalabilidad de SQLite**: SQLite es adecuado para este challenge, pero en un entorno de producción con alta concurrencia, podría convertirse en un cuello de botella. La migración a un SGBD como PostgreSQL sería necesaria.
- **Rendimiento del Algoritmo**: La comparación de strings puede ser computacionalmente costosa. Si el volumen de peticiones es alto, podría ser necesario optimizar el algoritmo o introducir un sistema de caché.

