import pandas as pd


def limpiar_datos(df_total):
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