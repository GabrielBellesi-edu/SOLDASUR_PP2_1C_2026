@echo off
:: instalar_marca.bat - Ejecutable rápido para instalar marcas en SOLDASUR (v5.0.0)

set brand_folder=%1
if "%brand_folder%"=="" (
    set /p brand_folder="Ingrese el nombre de la carpeta de la marca (que debe estar en 'nueva_marca/'): "
)

if "%brand_folder%"=="" (
    echo [ERROR] No se ingreso el nombre de la carpeta. abortando.
    pause
    exit /b 1
)

echo =======================================================================
echo Buscando carpeta: nueva_marca\%brand_folder%...
echo =======================================================================

if not exist "nueva_marca\%brand_folder%" (
    echo [ERROR] No existe la carpeta 'nueva_marca\%brand_folder%'.
    echo Por favor, crea la carpeta en 'nueva_marca\%brand_folder%' y coloca
    echo 'config.json' y 'catalog.json' adentro antes de continuar.
    echo.
    pause
    exit /b 1
)

:: Activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo Activando venv...
    call venv\Scripts\activate.bat
) else (
    echo [ADVERTENCIA] No se encontro 'venv\Scripts\activate.bat'.
    echo Se intentara correr con el Python del sistema...
)

:: Ejecutar instalador
python app/modules/escalamiento/install_brand.py %brand_folder%

pause
