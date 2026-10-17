import os
import re
from io import BytesIO
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