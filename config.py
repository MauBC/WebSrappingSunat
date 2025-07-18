import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_NAME")  
DB_USERNAME = os.getenv("DB_USER")  
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER_CREACION = os.getenv("CREATED_BY")  
