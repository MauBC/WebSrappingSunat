import pyodbc
from config import DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD

def get_connection():
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={DB_SERVER};'
        f'DATABASE={DB_DATABASE};'
        f'UID={DB_USERNAME};'
        f'PWD={DB_PASSWORD}'
    )
    return conn

def insertar_tipo_cambio(fecha, compra, venta, user_creacion):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "{CALL InsertarTipoCambio (?, ?, ?, ?)}",
        (fecha, compra, venta, user_creacion)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
