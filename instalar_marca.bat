@echo off
:: instalar_marca.bat - Ejecutable rápido para instalar marcas en SOLDASUR (v5.0.2)

set brand_name=%1
if "%brand_name%"=="" (
    set /p brand_name="Ingrese el nombre de la marca (ej: Durlock): "
)

if "%brand_name%"=="" (
    echo [ERROR] No se ingreso el nombre de la marca. Abortando.
    pause
    exit /b 1
)

echo =======================================================================
echo Buscando carpeta: scraping\data_raw\%brand_name%...
echo =======================================================================

if not exist "scraping\data_raw\%brand_name%" (
    echo [ERROR] No existe la carpeta 'scraping\data_raw\%brand_name%'.
    echo Por favor, crea la carpeta en 'scraping\data_raw\<marca_lower>' y coloca
    echo 'config.json' y '<marca_lower>_catalog.json' adentro antes de continuar.
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
python app/modules/escalamiento/install_brand.py %brand_name%

pause
