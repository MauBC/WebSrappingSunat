import argparse
from datetime import datetime
from utils.funciones import obtener_tipo_cambio_mes
from db import insertar_tipo_cambio
from config import DB_USER_CREACION

if __name__ == "__main__":
    hoy = datetime.today()

    parser = argparse.ArgumentParser(description="Consultar tipo de cambio SUNAT")
    parser.add_argument("anio", type=int, nargs="?", default=hoy.year, help="Año (ejemplo: 2025)")
    parser.add_argument("mes", type=int, nargs="?", default=hoy.month, help="Mes (1-12)")
    parser.add_argument("dia", type=int, nargs="?", default=hoy.day, help="Día (1-31)")

    args = parser.parse_args()

    # Obtener tipo de cambio
    resultado = obtener_tipo_cambio_mes(args.anio, args.mes, args.dia)
    print("Tipo de cambio obtenido:", resultado)

    fecha_db = datetime.strptime(resultado['fecha'], '%d/%m/%Y').date()
    valor_compra = float(resultado['compra'])
    valor_venta = float(resultado['venta'])

    # Insertar en la base de datos
    insertar_tipo_cambio(fecha_db, valor_compra, valor_venta, DB_USER_CREACION)
    print(f"✅ Registro insertado en dbo.TipoCambio para fecha {fecha_db}")
