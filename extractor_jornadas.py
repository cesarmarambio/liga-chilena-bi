import os
import requests
import mysql.connector
import logging
from mysql.connector import Error
from dotenv import load_dotenv

# 1. CONFIGURACIÓN INICIAL Y LOGGING
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

JORNADA_ACTUAL = 15

def obtener_diccionario_equipos(cursor) -> dict:
    """Consulta la base de datos y retorna un diccionario {id_api: id_equipo_local}"""
    cursor.execute("SELECT id_api, id_equipo FROM dim_equipo WHERE id_api IS NOT NULL")
    return {row[0]: row[1] for row in cursor.fetchall()}

def ejecutar_pipeline():
    logger.info(f"--- INICIANDO ETL: JORNADA {JORNADA_ACTUAL} ---")
    conexion = None
    
    try:
        # 2. CONEXIÓN A BASE DE DATOS (Con variables seguras)
        logger.info("Conectando a MySQL local...")
        conexion = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )
        cursor = conexion.cursor()

        # 3. CONSTRUCCIÓN DINÁMICA DEL DICCIONARIO
        logger.info("Construyendo homologación de equipos desde la dimensión...")
        homologacion_equipos = obtener_diccionario_equipos(cursor)
        
        if not homologacion_equipos:
            logger.warning("No se encontraron IDs de la API en dim_equipo. Abortando.")
            return

        # 4. EXTRACCIÓN (Desde RapidAPI)
        logger.info("Extrayendo datos en vivo de la API...")
        api_url = f"https://{os.getenv('RAPIDAPI_HOST')}/football-get-standing-all"
        headers = {
            "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
            "x-rapidapi-host": os.getenv('RAPIDAPI_HOST')
        }
        
        respuesta = requests.get(api_url, headers=headers, params={"leagueid": "273"})
        respuesta.raise_for_status() # Lanza error si el HTTP no es 200 OK
        
        lista_equipos = respuesta.json().get("response", {}).get("standing", [])

        # 5. TRANSFORMACIÓN Y CARGA
        logger.info("Transformando e insertando registros...")
        query_insert = """
            INSERT INTO fact_posiciones 
            (id_posicion, id_equipo, id_jornada, posicion_tabla, puntos, partidos_jugados, 
             victorias, empates, derrotas, goles_favor, goles_contra, diferencia_goles)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        filas_insertadas = 0
        
        for equipo in lista_equipos:
            # IMPORTANTE: Revisa en la respuesta JSON cómo se llama el campo de ID del equipo
            id_equipo_api = equipo.get("id") 
            id_equipo_local = homologacion_equipos.get(id_equipo_api)
            
            if not id_equipo_local:
                logger.debug(f"Equipo API ID {id_equipo_api} no mapeado. Saltando.")
                continue
                
            goles_str = equipo["scoresStr"].split("-")
            goles_favor = int(goles_str[0])
            goles_contra = int(goles_str[1])
            posicion = equipo["idx"]
            
            valores = (
                posicion,          # id_posicion (ahora parte de la llave compuesta)
                id_equipo_local, 
                JORNADA_ACTUAL, 
                posicion,          # posicion_tabla
                equipo["pts"], 
                equipo["played"], 
                equipo["wins"], 
                equipo["draws"], 
                equipo["losses"], 
                goles_favor, 
                goles_contra, 
                equipo["goalConDiff"]
            )
            
            cursor.execute(query_insert, valores)
            filas_insertadas += 1
            
        conexion.commit()
        logger.info(f"¡ETL FINALIZADO CON ÉXITO! {filas_insertadas} equipos actualizados.")

    except Error as e:
        logger.error(f"Error de Base de Datos: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión con la API: {e}")
    except Exception as e:
        logger.error(f"Error crítico en el pipeline: {e}")
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()
            logger.info("Conexión a base de datos cerrada.")

if __name__ == "__main__":
    ejecutar_pipeline()