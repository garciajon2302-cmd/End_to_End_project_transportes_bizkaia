import pandas as pd

# Limpiar datos de pasajeros
def limpiar_datos_pasajeros(df_total):
    #Convierte la fecha y renombra/elimina las columnas indicadas.
    df = df_total.copy()

    if df.empty:
        return df

    columnas_fecha = {"dia", "mes_anio", "hora"}
    faltantes = columnas_fecha.difference(df.columns)
    if faltantes:
        raise ValueError(
            f"Faltan columnas necesarias para crear fecha_hora: "
            f"{', '.join(sorted(faltantes))}"
        )

    df["Modo"] = df["Modo"].replace({
            "Autobus Interurbano": "Bizkaibus",
            "Autobus Urbano": "Bilbobus",
        })

    df["fecha_hora"] = pd.to_datetime(
        df["dia"].astype(str) + "/" +
        df["mes_anio"].astype(str) + " " +
        df["hora"].astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(2) +
        ":00",
        format="%d/%m/%Y %H:%M",
        errors="coerce",
    )

    df = df.drop(columns=["hora", "mes_anio", "dia"])
    df = df.rename(columns={
        "zona Entrada": "zona_entrada",
        "Zona Salida": "zona_salida",
        "numero": "pasajeros",
    })

    return df

# Función para limpiar las tarifas de la página de CTB
def limpiar_tarifas_barik(tablas):

    zonas_validas = {
        "Bilbobus",
        "Bizkaibus",
        "EuskoTren Línea General",
        "EuskoTren Atxuri",
        "EuskoTren Txorierri",
        "Metro Bilbao",
        "Renfe",
    }

    columnas = [
        "Año", "Zona", "Zona_1", "Zona_2",
        "Zona_3", "Zona_4", "Zona_5"
    ]

    numericas = [
        "Zona_1", "Zona_2", "Zona_3",
        "Zona_4", "Zona_5"
    ]

    df_limpios = []

    for anio, tabla in tablas:

        df = tabla.copy()

        # Normalizar los nombres de las columnas
        df.columns = [
            "Zona", "Zona_1", "Zona_2",
            "Zona_3", "Zona_4", "Zona_5"
        ]

        # Limpiar espacios en los nombres de las zonas
        df["Zona"] = (
            df["Zona"]
            .astype("string")
            .str.strip()
        )

        # Filtrar las zonas válidas
        df = df[df["Zona"].isin(zonas_validas)].copy()

        # Unificar nombres de operadores
        df["Zona"] = df["Zona"].replace({
            "EuskoTren Línea General": "EuskoTren",
            "EuskoTren Atxuri": "EuskoTren",
            "EuskoTren Txorierri": "Otros",
        })

        # Convertir importes de céntimos a euros
        for col in numericas:
            df[col] = (
                pd.to_numeric(
                    df[col],
                    errors="coerce"
                ) / 100
            ).fillna(0)

        # Añadir el año correspondiente
        df["Año"] = anio

        # Ordenar las columnas
        df = df[columnas]

        df_limpios.append(df)

        print(
            f"  OK: tarifas de {anio} limpiadas "
            f"({len(df)} filas)."
        )

    # Concatenar todas las tablas
    df_resultado = pd.concat(
        df_limpios,
        ignore_index=True
    )

    return df_resultado