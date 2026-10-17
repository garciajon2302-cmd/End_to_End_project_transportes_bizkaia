import os

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg import sql


COLUMNAS_DATAFRAME = (
    "zona_entrada",
    "zona_salida",
    "Modo",
    "pasajeros",
    "fecha_hora",
)
COLUMNAS_POSTGRES = (
    "zona_entrada",
    "zona_salida",
    "modo",
    "pasajeros",
    "fecha_hora",
)
CLAVE_PRIMARIA = ("fecha_hora", "zona_entrada", "zona_salida")


def cargar_datos(df_total):
    # Inserta viajes nuevos e ignora los ya registrados según la clave primaria.
    # Carga las variables de conexión definidas en el archivo .env.
    load_dotenv()
    variables_entorno = {
        "USERNAME_DB": ("user", os.getenv("USERNAME_DB")),
        "PASSWORD_DB": ("password", os.getenv("PASSWORD_DB")),
        "HOST_DB": ("host", os.getenv("HOST_DB")),
        "PORT_DB": ("port", os.getenv("PORT_DB")),
        "NAME_DB": ("dbname", os.getenv("NAME_DB")),
    }
    # Comprueba que estén definidas todas las credenciales de Postgres.
    faltantes = [
        variable
        for variable, (_, valor) in variables_entorno.items()
        if not valor
    ]
    if faltantes:
        raise ValueError(
            f"Faltan variables de entorno para PostgreSQL: {', '.join(faltantes)}"
        )
    variables_db = {clave: valor for clave, valor in variables_entorno.values()}

    # Obtiene el nombre de la tabla desde el archivo .env.
    table_name = os.getenv("NAME_DB_TABLE")
    if not table_name:
        raise ValueError("Falta la variable de entorno NAME_DB_TABLE.")

    # Verifica que el DataFrame incluya todas las columnas necesarias para la tabla.
    columnas_faltantes = [
        columna for columna in COLUMNAS_DATAFRAME if columna not in df_total.columns
    ]
    if columnas_faltantes and not df_total.empty:
        raise ValueError(
            f"Faltan columnas requeridas para PostgreSQL: "
            f"{', '.join(columnas_faltantes)}"
        )

    # Prepara una inserción parametrizada e ignora filas que ya existan
    # según la clave primaria compuesta.
    consulta = sql.SQL(
        "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO NOTHING"
    ).format(
        sql.Identifier("public", table_name),
        sql.SQL(", ").join(map(sql.Identifier, COLUMNAS_POSTGRES)),
        sql.SQL(", ").join(sql.Placeholder() for _ in COLUMNAS_POSTGRES),
        sql.SQL(", ").join(map(sql.Identifier, CLAVE_PRIMARIA)),
    )

    # Abre una transacción: si la inserción falla, PostgreSQL revierte los cambios.
    variables_db["port"] = int(variables_db["port"])
    try:
        with psycopg.connect(**variables_db) as conn:
            if not df_total.empty:
                with conn.cursor() as cursor:
                    # Envía las filas a medida que Psycopg las consume, sin crear
                    # una segunda lista con todos los datos del DataFrame.
                    filas = (
                        tuple(
                            None
                            if pd.isna(valor)
                            else valor.to_pydatetime()
                            if isinstance(valor, pd.Timestamp)
                            else valor.item()
                            if hasattr(valor, "item")
                            else valor
                            for valor in fila
                        )
                        for fila in df_total[list(COLUMNAS_DATAFRAME)].itertuples(
                            index=False, name=None
                        )
                    )
                    cursor.executemany(consulta, filas)
    except psycopg.OperationalError as error:
        # Informa del fallo de conexión y lo propaga para que no pase inadvertido.
        print(
            "ALERTA: no se pudo conectar con PostgreSQL "
            f"en {variables_db['host']}:{variables_db['port']}/"
            f"{variables_db['dbname']}: {error}"
        )
        raise ConnectionError(
            "No se pudo conectar con PostgreSQL. Revisa el servicio y las "
            "variables de conexión."
        ) from error

    # Devuelve el mismo DataFrame para mantener el comportamiento del orquestador.
    return df_total
