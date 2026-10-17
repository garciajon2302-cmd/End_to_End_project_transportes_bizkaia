import os
import re
from io import BytesIO, StringIO
from urllib.parse import unquote, urlparse
import pandas as pd
import requests
from dotenv import load_dotenv


HOJA = "zonas_Modo_dia_hora"

MESES = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}


def extraer_datos(base_url=None):
    #Descarga y concatena los Excel de transporte para la hoja indicada.
    load_dotenv()
    base_url = (base_url or os.getenv("URL") or "").rstrip("/")

    if not base_url:
        raise ValueError("Configura la variable de entorno URL.")
    
    #Inicializar variables
    dataframes = []
    oks = 0
    nooks = 0

    with requests.Session() as session:
        response = session.get(f"{base_url}/package_list", timeout=30)
        response.raise_for_status()
        paquetes = response.json()["result"]

        filtered = [
            paquete for paquete in paquetes
            if "datos-transporte-ctb" in paquete.lower()
        ]

        print(f"Datasets encontrados: {len(filtered)}")
        for paquete in filtered:
            print(f"  - {paquete}")

        for paquete in filtered:
            match = re.search(
                r"datos-transporte-ctb-([a-záéíóú]+)-(\d{4})",
                paquete.lower(),
            )

            if not match or match.group(1) not in MESES:
                print(f"Se omite por no reconocer mes/año: {paquete}")
                continue

            mes_anio = f"{MESES[match.group(1)]}/{match.group(2)}"

            try:
                response = session.get(
                    f"{base_url}/package_show",
                    params={"id": paquete},
                    timeout=30,
                )
                response.raise_for_status()
                dataset = response.json()["result"]

                for resource in dataset.get("resources", []):
                    url = resource.get("url", "")
                    formato = (resource.get("format") or "").lower()
                    extension = unquote(urlparse(url).path).lower()

                    if not (
                        formato in {"xlsx", "xls"}
                        or extension.endswith((".xlsx", ".xls"))
                    ):
                        continue

                    try:
                        archivo = session.get(url, timeout=120)
                        archivo.raise_for_status()

                        df = pd.read_excel(
                            BytesIO(archivo.content),
                            sheet_name=HOJA,
                        )
                        df["mes_anio"] = mes_anio
                        dataframes.append(df)

                        print(f"OK: {paquete} | {mes_anio} | {len(df)} filas")
                        oks += 1
                    except Exception as error:
                        print(
                            f"Error en {paquete}, recurso "
                            f"{resource.get('name')}: {error}"
                        )
                        nooks += 1

            except Exception as error:
                print(f"Error al consultar {paquete}: {error}")
                nooks += 1

    if not dataframes:
        print("No se han podido leer archivos con esa hoja.")
        return pd.DataFrame()

    df_total = pd.concat(dataframes, ignore_index=True, sort=False)
    porcentaje = oks / (oks + nooks) * 100 if oks + nooks else 0

    print("\nConcatenación completada")
    print(f"Total filas: {len(df_total):,}")
    print(f"Total columnas: {len(df_total.columns)}")
    print(f"Porcentaje de recursos correctos: {porcentaje:.2f}%")

    return df_total

def extraer_tarifas_barik():
    urls = {
        2025: (
            "https://web.archive.org/web/20250428201536/"
            "https://www.ctb.eus/es/tarifas-barik"
        ),
        2024: (
            "https://web.archive.org/web/20240609064912/"
            "http://www.ctb.eus/es/tarifas-barik"
        ),
        2023: (
            "https://web.archive.org/web/20230326003158/"
            "https://www.ctb.eus/es/tarifas-barik"
        ),
        2022: (
            "https://web.archive.org/web/20220702090908/"
            "https://www.ctb.eus/es/tarifas-barik"
        ),
    }

    zonas_validas = {
        "Bilbobus",
        "Bizkaibus",
        "EuskoTren Línea General",
        "EuskoTren Atxuri",
        "EuskoTren Txorierri",
        "Metro Bilbao",
        "Renfe",
    }

    sesiones = requests.Session()
    sesiones.headers.update({"User-Agent": "Mozilla/5.0"})

    df = []

    for anio, url in urls.items():
        print(f"Descargando tarifas de {anio}...")

        try:
            respuesta = sesiones.get(url, timeout=30)
            respuesta.raise_for_status()

            # Extraer las tablas HTML
            tablas_html = pd.read_html(
                StringIO(respuesta.text),
                attrs={"class": "tarifas"}
            )

            # Alternativa si no se encuentran suficientes tablas
            if len(tablas_html) < 3:
                tablas_html = pd.read_html(
                    StringIO(respuesta.text)
                )

            # Identificar la tabla de tarifas
            candidatos = []

            for tabla in tablas_html:
                if tabla.shape[1] == 6:
                    primera_columna = (
                        tabla.iloc[:, 0]
                        .astype(str)
                        .str.strip()
                    )

                    if primera_columna.isin(
                        zonas_validas
                    ).any():
                        candidatos.append(tabla)

            if not candidatos:
                raise ValueError(
                    "No se encontró la tabla de tarifas "
                    "de seis columnas."
                )

            # Guardar la tabla original junto con su año
            df.append((anio, candidatos[0].copy()))

            print(
                f"  OK: tabla de {anio} extraída."
            )

        except Exception as error:
            raise RuntimeError(
                f"Error extrayendo las tarifas "
                f"de {anio}: {error}"
            ) from error

    return df