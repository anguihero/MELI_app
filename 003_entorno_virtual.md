### Activación del Entorno Virtual

A continuación se detallan los pasos para activar el entorno virtual y preparar el ambiente de desarrollo.

1.  **Navegar al directorio del proyecto**:
    Abra una terminal (PowerShell, CMD, Git Bash, etc.) y sitúese en la carpeta raíz del proyecto. Reemplace `"ruta/a/mi/proyecto"` con la ruta real.

    ```powershell
    cd "ruta/a/mi/proyecto"
    ```

2.  **Ajustar la política de ejecución en PowerShell (si es necesario)**:
    Si utiliza PowerShell, es posible que necesite permitir la ejecución de scripts para la sesión actual. Este comando solo afecta a la ventana de terminal activa.

    ```powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    ```

3.  **Activar el entorno virtual**:
    Ejecute el comando correspondiente a su terminal. El prompt de la terminal cambiará para indicar que el entorno está activo (generalmente mostrando `(.venv)`).

    -   **PowerShell**:
        ```powershell
        .venv\Scripts\Activate.ps1
        ```
    -   **CMD**:
        ```cmd
        .venv\Scripts\activate.bat
        ```
    -   **Git Bash**:
        ```bash
        source .venv/Scripts/activate
        ```

4.  **Instalar/actualizar dependencias**:
    Una vez activado el entorno, asegúrese de tener la última versión de `pip` y luego instale las dependencias del proyecto listadas en `requirements.txt`.

    ```bash
    # Actualizar pip
    python -m pip install --upgrade pip

    # Instalar dependencias
    pip install -r requirements.txt
    ```