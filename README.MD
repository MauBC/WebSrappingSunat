# Proyecto: Web Scraping SUNAT - Tipo de Cambio

Este proyecto automatiza la obtención del **tipo de cambio oficial (dólar a soles)** desde la web de la **SUNAT**, resolviendo el reCAPTCHA con Selenium y almacenando los datos en una base de datos **SQL Server**.

---

## **¿Qué hace el proyecto?**
1. **Obtiene un token reCAPTCHA con Selenium**:
   - Abre la web de SUNAT con un navegador controlado por Selenium.
   - Ejecuta el script de reCAPTCHA (usando la clave pública del sitio) para obtener un token válido.
   - Este token es necesario para consultar el tipo de cambio desde el endpoint oficial de SUNAT.

2. **Consulta el tipo de cambio vía API**:
   - Usa el endpoint:
     ```
     https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias/listarTipoCambio
     ```
   - Envía un JSON con el año, mes y token obtenido.

3. **Procesa los datos de compra y venta**:
   - Extrae los valores de compra (`C`) y venta (`V`) correspondientes a la fecha consultada.

4. **Guarda el resultado en SQL Server**:
   - Se conecta a una base de datos **SQL Server**.
   - Desactiva cualquier registro existente para la fecha (`EstadoRegistro = 0`).
   - Inserta el nuevo tipo de cambio con `EstadoRegistro = 1`.

---

## **Arquitectura**
```
WebScrappingSunat/
│
├── main.py              # Script principal, orquesta el flujo
├── db.py                # Funciones de conexión y queries a SQL Server
├── config.py            # Encargado de cargar las variables del archivo .env
├── utils/
│   ├── __init__.py
│   |── libraries.py     # librerias de scraping y API
│   └── funciones.py     # Funciones de scraping y API
├── .env                 # Variables sensibles (credenciales DB)
└── README.md            # Documentación del proyecto
```

---

## **Requisitos**
- **Python 3.11+**
- **Conda o virtualenv** para gestionar dependencias.
- Google Chrome instalado.
- ODBC Driver 17 for SQL Server (o 18).
- Librerías Python:
  ```bash
  pip install requests selenium python-dotenv pyodbc
  ```

---

## **Variables de entorno (.env)**
El archivo `.env` debe contener:
```
DB_SERVER=genesis.mkg.pe,1433
DB_DATABASE=POSMaster
DB_USERNAME=posmasteradmin
DB_PASSWORD=C0ntr@s3ñ@
DB_USER_CREACION=MauroBC
```

---

## **Uso**
### **1. Ejecutar el script principal**
```bash
python main.py 2025 6 15
```
- Parámetros: `Año Mes Día`.  
- Si no se especifican, usa la fecha actual.

### **2. ¿Qué hace el script?**
- Llama a `obtener_token_selenium()`:
  - Inicia un navegador Chrome controlado por Selenium.
  - Ejecuta el script `grecaptcha` para obtener el **token de validación**.
  - Cierra el navegador.
- Llama a `obtener_tipo_cambio_mes()`:
  - Envía un POST con el token a la API de SUNAT.
  - Procesa el JSON para obtener el tipo de cambio.
- Llama a `insertar_tipo_cambio()`:
  - Actualiza la tabla `dbo.TipoCambio` en SQL Server.
  - Inserta el nuevo registro con la fecha, compra, venta y usuario.

---

## **Consultas en SQL Server**
Para verificar los registros insertados:
```sql
USE POSMaster;
SELECT TOP 10 *
FROM dbo.TipoCambio
ORDER BY IdTipoCambio DESC;
```

---

## **Selenium y Captcha**
El proyecto resuelve el captcha así:
1. Abre el navegador con:
   ```python
   driver = webdriver.Chrome(options=options)
   driver.get("https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias")
   ```
2. Obtiene la clave pública del captcha:
   ```python
   site_key = driver.execute_script("return site_key_sunat;")
   ```
3. Ejecuta el captcha con JavaScript:
   ```python
   token = driver.execute_async_script("""
       var callback = arguments[arguments.length - 1];
       grecaptcha.ready(function() {
           grecaptcha.execute(arguments[0], {action: 'token'}).then(callback);
       });
   """, site_key)
   ```
4. Devuelve el token para realizar la consulta a la API.

---

## **Notas**
- El scraping de SUNAT requiere resolver el reCAPTCHA; Selenium es usado para simular un navegador real.
- La lógica de inserción en base de datos puede migrarse a una **stored procedure** en SQL Server para mayor eficiencia.
Desarrollado para automatizar la consulta de tipo de cambio de la SUNAT y almacenarlo en SQL Server.
