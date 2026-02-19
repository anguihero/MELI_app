
# MELI Matches Challenge

---

- **Autor:** https://github.com/anguihero & https://www.linkedin.com/in/amms1989/
- **Versión:** 2.0.0
- **Fecha:** 2026/2/18

---


## 🎯 Objetivo

Desarrollar una **API REST robusta y escalable** que implementa un algoritmo de similitud de textos con persistencia en base de datos, validación de estados y un sistema completo de logging. Este proyecto demuestra competencias en arquitectura de software, desarrollo backend y buenas prácticas de ingeniería.

## ✨ Logros Principales

- ✅ **API escalable** con FastAPI, 7 endpoints funcionales y documentación automática (Swagger UI)
- ✅ **Algoritmo inteligente** de comparación de textos con caché de resultados positivos
- ✅ **Base de datos robusta** con 3 tablas (items, matches, matches_backup) y control de estados
- ✅ **Cobertura de pruebas** >80% (11 unitarias + 21 pruebas E2E validadas)
- ✅ **Containerización completa** con Docker Compose para despliegue inmediato
- ✅ **Logging estructurado** y documentación técnica exhaustiva

## 📚 Documentación

Explora los detalles técnicos en:

| Documento | Contenido |
|-----------|----------|
| [📋 Plan de Trabajo](./docs/PLAN_TRABAJO.md) | Etapas, criterios de aceptación y checklist completado |
| [🏗️ Arquitectura](./docs/ARQUITECTURA.md) | Diseño de 3 capas, estructura de directorios y flujos |
| [📊 Schema Base de Datos](./docs/SCHEMA_BD.md) | Modelos, relaciones y descripción de tablas |
| [🚀 Guía de Instalación](./INSTALLATION.md) | Setup local, Docker, variables de entorno |
| [📡 Referencia API](./docs/API_REFERENCE.md) | Endpoints, ejemplos curl y códigos de respuesta |
| [🧪 Testing](./docs/TESTING.md) | Estrategia de pruebas, ejecución y resultados |

## 🚀 Inicio Rápido

1. **Navegar al directorio del proyecto**:
    Abra una terminal (PowerShell, CMD, Git Bash, etc.) y sitúese en la carpeta raíz del proyecto.

    ```powershell
    cd "ruta/a/mi/proyecto/services/"
    ```

2. **Desplegar con Docker Compose**:

    ```bash
    docker-compose up
    ```

3. **Verificar la API**:
    - API disponible en http://localhost:8000
    - Documentación interactiva (Swagger UI) en http://localhost:8000/docs


---

## 🧪 Documentación de Pruebas

Este archivo contiene la documentación y pruebas de la aplicación MELI. 

- ruta : `/tests/pruebas_api.ipynb`

### Ubicación del Notebook de Pruebas
El notebook de pruebas se encuentra en el directorio del proyecto y proporciona:

- **Ejemplos de uso** de las funcionalidades principales de la aplicación
- **Casos de prueba** que demuestran el comportamiento esperado
- **Guía práctica** para entender cómo utilizar la aplicación

### Cómo usar el Notebook
1. Navega al notebook de pruebas en la carpeta del proyecto
2. Ejecuta las celdas de forma secuencial para ver ejemplos prácticos
3. Modifica los parámetros según tus necesidades
4. Consulta los resultados y outputs para validar el funcionamiento

### Referencia
Para entender completamente las capacidades y el uso correcto de la aplicación MELI, se recomienda revisar y ejecutar el notebook de pruebas incluido en este repositorio.
# revisión de pruebas en notebook test


---

**Proyecto completado con éxito** | Python 3.12 | FastAPI | SQLAlchemy | PostgreSQL
