import os

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg import sql


COLUMNAS_DATAFRAME_PASAJEROS = (
    "zona_entrada",
    "zona_salida",
    "Modo",
    "pasajeros",
    "fecha_hora",
)
COLUMNAS_POSTGRES_PASAJEROS = (
    "zona_entrada",
    "zona_salida",
    "modo",
    "pasajeros",
    "fecha_hora",
)
CLAVE_UNICA_PASAJEROS = ("fecha_hora", "zona_entrada", "zona_salida", "modo")

COLUMNAS_DATAFRAME_TARIFAS = (
    "Año",
    "Zona",
    "Zona_1",
    "Zona_2",
    "Zona_3",
    "Zona_4",
    "Zona_5",
)
COLUMNAS_POSTGRES_TARIFAS = (
    "año",
    "modo",
    "zona_1",
    "zona_2",
    "zona_3",
    "zona_4",
    "zona_5",
)
CLAVE_UNICA_TARIFAS = ("año", "modo")


def _obtener_variables_db():
    load_dotenv()
    variables_entorno = {
        "USERNAME_DB": ("user", os.getenv("USERNAME_DB")),
        "PASSWORD_DB": ("password", os.getenv("PASSWORD_DB")),
        "HOST_DB": ("host", os.getenv("HOST_DB")),
        "PORT_DB": ("port", os.getenv("PORT_DB")),
        "NAME_DB": ("dbname", os.getenv("NAME_DB")),
    }
    faltantes = [
        variable
        for variable, (_, valor) in variables_entorno.items()
        if not valor
    ]
    if faltantes:
        raise ValueError(
            f"Faltan variables de entorno para PostgreSQL: {', '.join(faltantes)}"
        )

    variables_db = {
        clave: valor for clave, valor in variables_entorno.values()
    }
    try:
        variables_db["port"] = int(variables_db["port"])
    except ValueError as error:
        raise ValueError("PORT_DB debe ser un número entero.") from error
    return variables_db


def _obtener_nombre_tabla(variable_entorno):
    table_name = os.getenv(variable_entorno)
    if not table_name:
        raise ValueError(f"Falta la variable de entorno {variable_entorno}.")
    return table_name


def cargar_datos_pasajeros(df_total):
    # Inserta viajes nuevos y actualiza el recuento de los ya registrados.
    variables_db = _obtener_variables_db()
    table_name = _obtener_nombre_tabla("NAME_DB_TABLE_PASAJEROS")

    # Verifica que el DataFrame incluya todas las columnas necesarias para la tabla.
    columnas_faltantes = [
        columna for columna in COLUMNAS_DATAFRAME_PASAJEROS if columna not in df_total.columns
    ]
    if columnas_faltantes and not df_total.empty:
        raise ValueError(
            f"Faltan columnas requeridas para PostgreSQL: "
            f"{', '.join(columnas_faltantes)}"
        )

    # Usa las dimensiones del viaje como identidad y actualiza pasajeros, que
    # es un valor medido y no parte de la clave.
    consulta = sql.SQL(
        "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) "
        "DO UPDATE SET {} = EXCLUDED.{}"
    ).format(
        sql.Identifier("public", table_name),
        sql.SQL(", ").join(map(sql.Identifier, COLUMNAS_POSTGRES_PASAJEROS)),
        sql.SQL(", ").join(sql.Placeholder() for _ in COLUMNAS_POSTGRES_PASAJEROS),
        sql.SQL(", ").join(map(sql.Identifier, CLAVE_UNICA_PASAJEROS)),
        sql.Identifier("pasajeros"),
        sql.Identifier("pasajeros"),
    )

    # Abre una transacción: si la inserción falla, PostgreSQL revierte los cambios.
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
                        for fila in df_total[list(COLUMNAS_DATAFRAME_PASAJEROS)].itertuples(
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


def cargar_tarifas_viajes(df_tarifas):
    # Carga las tarifas limpias en la tabla tarifas_viajes.
    columnas_faltantes = [
        columna
        for columna in COLUMNAS_DATAFRAME_TARIFAS
        if columna not in df_tarifas.columns
    ]
    if columnas_faltantes and not df_tarifas.empty:
        raise ValueError(
            f"Faltan columnas requeridas para tarifas_viajes: "
            f"{', '.join(columnas_faltantes)}"
        )

    variables_db = _obtener_variables_db()
    table_name = _obtener_nombre_tabla("NAME_DB_TABLE_TARIFAS")

    consulta = sql.SQL(
        "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO UPDATE SET {}"
    ).format(
        sql.Identifier("public", table_name),
        sql.SQL(", ").join(map(sql.Identifier, COLUMNAS_POSTGRES_TARIFAS)),
        sql.SQL(", ").join(sql.Placeholder() for _ in COLUMNAS_POSTGRES_TARIFAS),
        sql.SQL(", ").join(map(sql.Identifier, CLAVE_UNICA_TARIFAS)),
        sql.SQL(", ").join(
            sql.SQL("{} = EXCLUDED.{}").format(
                sql.Identifier(columna),
                sql.Identifier(columna),
            )
            for columna in COLUMNAS_POSTGRES_TARIFAS
            if columna not in CLAVE_UNICA_TARIFAS
        ),
    )

    try:
        with psycopg.connect(**variables_db) as conn:
            if not df_tarifas.empty:
                with conn.cursor() as cursor:
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
                        for fila in df_tarifas[
                            list(COLUMNAS_DATAFRAME_TARIFAS)
                        ].itertuples(index=False, name=None)
                    )
                    cursor.executemany(consulta, filas)
    except psycopg.OperationalError as error:
        print(
            "ALERTA: no se pudo conectar con PostgreSQL "
            f"en {variables_db['host']}:{variables_db['port']}/"
            f"{variables_db['dbname']}: {error}"
        )
        raise ConnectionError(
            "No se pudo conectar con PostgreSQL. Revisa el servicio y las "
            "variables de conexión."
        ) from error

    return df_tarifas
