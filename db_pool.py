# db_pool.py
import logging
from logging.handlers import RotatingFileHandler
import os
#import mysql.connector
from mysql.connector import pooling
import pandas as pd
from sqlalchemy import create_engine

# Enable logging

logger = logging.getLogger(__name__)  # No necesitas configurar logging aquí

class Database:
    def __init__(self, db_user, db_password, db_host, db_database, db_port, pool_size):

        db_config= {
            "user": f"{db_user}",
            "password": f"{db_password}",
            "host": f"{db_host}",
            "database": f"{db_database}",
            "port": f"{db_port}"
            }

                #---------- Archivo de Configuración -----------
        # Crear un pool de conexiones
        self.pool = pooling.MySQLConnectionPool(pool_name="mypool",
                                                pool_size=pool_size,
                                                **db_config)
  
        cadena_conexion=f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}'

        self.engine = create_engine(cadena_conexion, pool_size=5)

    def ejecutar_consulta(self, consulta, parametros=None, columns=None):

        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            cursor.execute(consulta, parametros)
            resultado = cursor.fetchall()

            # Si se especificaron columnas y no hay resultados, crea un DataFrame vacío con esas columnas
            if columns:
                if resultado:  # Si hay resultados
                    resultado = pd.DataFrame(resultado, columns=columns)
                else:  # Si no hay resultados
                    resultado = pd.DataFrame(columns=columns)  # DataFrame vacío con las columnas especificadas
            else:
                resultado = pd.DataFrame(resultado)  # DataFrame sin columnas si no se especificaron
            
        except Exception as e:
            logger.error(f"BASE de DATOS: Se presenta el error: {e}")
            logger.error(f"BASE de DATOS: Al ejecutar ejecutar consulta: {consulta}")
            resultado = pd.DataFrame(columns=columns) if columns else pd.DataFrame()  # Devuelve DataFrame vacío en caso de error       
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        return resultado
    
    def ejecutar_actualizacion(self, consulta, parametros=None):
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            cursor.execute(consulta, parametros)
            conn.commit()  # Para las operaciones que modifiquen datos
        except Exception as e:
            logger.error(f"BASE de DATOS: Se presenta el error: {e}")
            logger.error(f"BASE de DATOS: Al ejecutar ejecutar consulta: {consulta}")          
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def insertar_dataframe(self, df, tabla, if_exists='append'):
        """ Inserta un DataFrame en una tabla MySQL.
        - df: el DataFrame a insertar.
        - tabla: el nombre de la tabla de destino.
        - if_exists: qué hacer si la tabla ya existe. Opciones: 'fail', 'replace', 'append' (default: 'append').
        """
        conn=None
        try:
            with self.engine.begin() as conn:
                # Usar SQLAlchemy para insertar el DataFrame en la tabla
                df.to_sql(name=tabla, con=conn, if_exists=if_exists, index=False)
        
            logger.info(f"BASE de DATOS: Datos insertados correctamente en la tabla {tabla}.")
        except Exception as e:
            logger.error(f"BASE de DATOS: Error al insertar DF: {e}")
            
            if conn is not None and conn.in_transaction():
                conn.rollback()
        finally:
            if conn is not None:
                conn.close()