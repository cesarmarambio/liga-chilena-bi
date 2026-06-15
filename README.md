# Pipeline ETL & Business Intelligence - Liga Chilena 

Este proyecto es una solución *end-to-end* de Data Engineering y Business Intelligence que extrae, transforma y visualiza los datos de rendimiento del Campeonato Nacional de Fútbol Chileno en tiempo real.

## Arquitectura del Proyecto

El flujo de datos está diseñado bajo las mejores prácticas de la industria, asegurando modularidad, seguridad y escalabilidad:

1. **Extracción (API REST):** Script en Python que consume la API de *Free API Live Football Data* para obtener las posiciones actualizadas por jornada.
2. **Transformación & Carga (Python + MySQL):**
   * Cruce dinámico de IDs de equipos desde una dimensión en la base de datos (evitando *hardcoding*).
   * Ingesta automatizada hacia un modelo en estrella (Star Schema) en MySQL.
   * Implementación de lógica **Upsert** (`ON DUPLICATE KEY UPDATE`) para manejar reprocesos sin duplicar registros.
3. **Visualización (Power BI):** Dashboard interactivo conectado al motor SQL, con modelado de datos y cálculos DAX avanzados para el análisis de rendimiento, brechas de puntos y diferencias de goles.

## Tecnologías y Librerías Utilizadas

* **Python 3.x:** Motor principal del pipeline ETL.
* **Requests:** Para el consumo de la API REST.
* **MySQL Connector:** Para la interacción nativa con la base de datos.
* **Python-dotenv:** Para la gestión segura de variables de entorno y credenciales.
* **Argparse:** Para la ejecución parametrizada por Interfaz de Línea de Comandos (CLI).
* **MySQL:** Motor de base de datos relacional (Data Warehouse).
* **Power BI:** Capa analítica y de visualización.

## Cómo ejecutar el pipeline ETL

El script está preparado para ejecutarse por consola recibiendo el número de jornada como parámetro.

1. Clona este repositorio.
2. Crea un archivo `.env` en la raíz del proyecto con tus credenciales.
3. Instala las dependencias necesarias ejecutando en tu terminal:

    ```bash
    pip install requests mysql-connector-python python-dotenv
    ```

4. Ejecuta el pipeline indicando la jornada deseada mediante el flag `-j`:

    ```bash
    python extractor_jornadas.py -j 15
    ```

## Seguridad

Se implementó un archivo `.gitignore` para excluir el archivo `.env`, garantizando que las credenciales de base de datos y API Keys nunca se expongan en el repositorio.