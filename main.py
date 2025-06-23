import requests
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime
import pyodbc


# ============================================================
# FUNCIÓN: obtener_token_selenium
# ------------------------------------------------------------
# Usa Selenium para abrir el sitio de SUNAT, ejecutar grecaptcha
# y obtener un token válido que autoriza la consulta de tipo de cambio.
# ============================================================
def obtener_token_selenium():
    # Configura opciones de Chrome para parecer navegador humano
    options = Options()
    # Desactiva bandera que revela que es un bot
    options.add_argument("--disable-blink-features=AutomationControlled")
    #options.add_argument("--headless")

    # Inicializa el navegador Chrome
    driver = webdriver.Chrome(options=options)
    
    # Abre la página oficial de tipo de cambio de SUNAT
    driver.get("https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias")
    
    # Espera unos segundos para que cargue reCAPTCHA
    time.sleep(2)
    
    # Ejecuta JavaScript para leer la clave pública del captcha
    site_key = driver.execute_script("return site_key_sunat;")
    
    # Ejecuta el captcha usando la clave leída, obtiene el token
    token = driver.execute_async_script("""
        var callback = arguments[arguments.length - 1];
        grecaptcha.ready(function() {
            grecaptcha.execute(arguments[0], {action: 'token'}).then(callback);
        });
    """, site_key)
    
    # Cierra el navegador
    driver.quit()
    
    # Devuelve el token obtenido
    return token

# ============================================================
# FUNCIÓN: obtener_tipo_cambio_mes
# ------------------------------------------------------------
# Obtiene el tipo de cambio de compra y venta de dólares a soles
# para un día específico, usando el JSON oficial de SUNAT.
#
# Parámetros:
#   anio - Año (ejemplo: 2025)
#   mes  - Mes (1=Enero, 6=Junio, etc)
#   dia  - Día del mes (1 a 31)
#
# Retorna:
#   Diccionario con fecha, compra y venta; o mensaje de error.
# ============================================================
def obtener_tipo_cambio_mes(anio, mes, dia):
    # Obtiene el token CAPTCHA válido usando Selenium
    token = obtener_token_selenium()
    
    # URL del endpoint JSON oficial de SUNAT
    url = "https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias/listarTipoCambio"
    
    # Payload de la consulta: ojo que mes en la API es base 0 (enero=0)
    payload = {
        "anio": anio,
        "mes": mes - 1,
        "token": token
    }
    
    # Cabeceras HTTP para que el servidor no bloquee la conexión
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias",
        "User-Agent": "Mozilla/5.0"
    }
    
    # Realiza la petición POST con payload y cabeceras correctas
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    # Lanza error si la respuesta no es 200 OK
    response.raise_for_status()
    
    # Decodifica la respuesta como JSON (es una lista de días)
    data = response.json()
    
    # Formatea la fecha como la entrega SUNAT: "DD/MM/YYYY"
    fecha_buscar = f"{dia:02}/{mes:02}/{anio}"
    
    # Busca el valor de compra: registro con fecha y codTipo = "C"
    compra = next(
        (d["valTipo"] for d in data 
         if d["fecPublica"] == fecha_buscar and d["codTipo"] == "C"),
        None
    )
    
    # Busca el valor de venta: registro con fecha y codTipo = "V"
    venta = next(
        (d["valTipo"] for d in data 
         if d["fecPublica"] == fecha_buscar and d["codTipo"] == "V"),
        None
    )
    
    # Si encuentra alguno, devuelve diccionario con info
    if compra or venta:
        return {
            "fecha": fecha_buscar,
            "compra": compra,
            "venta": venta
        }
    else:
        # Si no hay datos para esa fecha, mensaje amigable
        return f"No hay datos para {fecha_buscar}"


# ============================================================

if __name__ == "__main__":
    #python tipo_cambio.py 2025 6 15

    # Fecha de hoy
    hoy = datetime.today()

    # Configura argparse con valores por defecto
    parser = argparse.ArgumentParser(description="Consultar tipo de cambio SUNAT")

    parser.add_argument(
        "anio",
        type=int,
        nargs="?", ## Significa: argumento opcional, máximo uno.
        default=hoy.year,
        help="Año (ejemplo: 2025)"
    )

    parser.add_argument(
        "mes",
        type=int,
        nargs="?", ## Significa: argumento opcional, máximo uno.
        default=hoy.month,
        help="Mes (1-12)"
    )

    parser.add_argument(
        "dia",
        type=int, 
        nargs="?", ## Significa: argumento opcional, máximo uno.
        default=hoy.day,
        help="Día (1-31)"
    )

    args = parser.parse_args()
    
    #resultado = obtener_tipo_cambio_mes(2025, 6, 21)


    # === OBTENER TIPO DE CAMBIO ===
    resultado = obtener_tipo_cambio_mes(args.anio, args.mes, args.dia)

    print("Tipo de cambio obtenido:", resultado)

    # === DATOS DEL TIPO DE CAMBIO ===
    fecha_str = resultado['fecha']  # '21/06/2025'
    fecha_db = datetime.strptime(fecha_str, '%d/%m/%Y').date()
    valor_compra = float(resultado['compra'])
    valor_venta = float(resultado['venta'])

    # === CONEXION A SQL SERVER ===
    server = 'genesis.mkg.pe,1433'
    database = 'POSMaster'
    username = 'posmasteradmin'
    password = 'C0ntr@s3ñ@'

    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )

    cursor = conn.cursor()

    # === ACTUALIZAR Y INSERTAR ===
    print(f"🔄 Desactivando registros existentes para fecha {fecha_db}...")
    update_query = """
    UPDATE dbo.TipoCambio
    SET EstadoRegistro = 0
    WHERE Fecha = ? AND EstadoRegistro = 1;
    """
    cursor.execute(update_query, fecha_db)

    query = """
    INSERT INTO dbo.TipoCambio
        (Fecha, ValorCompra, ValorVenta, EstadoRegistro, UsuarioCreacion, FechaHoraCreacion)
    VALUES (?, ?, ?, ?, ?, GETDATE());
    """

    params = (
        fecha_db,
        valor_compra,
        valor_venta,
        1,                 # EstadoRegistro = activo
        'MauroBC'    # UsuarioCreacion
    )

    cursor.execute(query, params)
    conn.commit()

    print(f"✅ Registro insertado en dbo.TipoCambio para fecha {fecha_db}")

    cursor.close()
    conn.close()


    print(resultado)
