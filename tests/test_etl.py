import pandas as pd
import pytest

from src import carga, extraccion, limpieza, orquestador


def test_limpiar_pasajeros_transforma_columnas_fechas_y_modos():
    entrada = pd.DataFrame({
        "dia": ["01", "02"],
        "mes_anio": ["03/2024", "03/2024"],
        "hora": [8, "9.0"],
        "Modo": ["Autobus Interurbano", "Autobus Urbano"],
        "zona Entrada": ["A", "B"],
        "Zona Salida": ["B", "C"],
        "numero": [10, 20],
    })

    resultado = limpieza.limpiar_datos_pasajeros(entrada)

    assert resultado["Modo"].tolist() == ["Bizkaibus", "Bilbobus"]
    assert resultado["zona_entrada"].tolist() == ["A", "B"]
    assert resultado["zona_salida"].tolist() == ["B", "C"]
    assert resultado["pasajeros"].tolist() == [10, 20]
    assert resultado["fecha_hora"].tolist() == [
        pd.Timestamp("2024-03-01 08:00"),
        pd.Timestamp("2024-03-02 09:00"),
    ]
    assert not {"dia", "mes_anio", "hora", "numero"}.intersection(resultado.columns)
    # La limpieza no modifica el DataFrame de entrada.
    assert "dia" in entrada.columns


def test_limpiar_pasajeros_falla_si_faltan_columnas_de_fecha():
    entrada = pd.DataFrame({"Modo": ["Bilbobus"]})

    with pytest.raises(ValueError, match="Faltan columnas necesarias"):
        limpieza.limpiar_datos_pasajeros(entrada)


def test_limpiar_pasajeros_devuelve_dataframe_vacio():
    entrada = pd.DataFrame()

    resultado = limpieza.limpiar_datos_pasajeros(entrada)

    assert resultado.empty


def test_limpiar_tarifas_filtra_normaliza_y_convierte_importes():
    tabla = pd.DataFrame([
        ["Bilbobus", "120", "250", "texto", None, "500"],
        ["EuskoTren Línea General", "100", "200", "300", "400", "500"],
        ["Operador desconocido", "100", "100", "100", "100", "100"],
    ])

    resultado = limpieza.limpiar_tarifas_barik([(2025, tabla)])

    assert resultado["Zona"].tolist() == ["Bilbobus", "EuskoTren"]
    assert resultado["Año"].tolist() == [2025, 2025]
    assert resultado.loc[0, "Zona_1"] == pytest.approx(1.2)
    assert resultado.loc[0, "Zona_2"] == pytest.approx(2.5)
    assert resultado.loc[0, "Zona_3"] == 0
    assert resultado.loc[0, "Zona_4"] == 0
    assert resultado.columns.tolist() == [
        "Año", "Zona", "Zona_1", "Zona_2", "Zona_3", "Zona_4", "Zona_5"
    ]


def test_extraccion_pasajeros_falla_si_no_hay_url(monkeypatch):
    monkeypatch.delenv("URL", raising=False)
    monkeypatch.setattr(extraccion, "load_dotenv", lambda: None)

    with pytest.raises(ValueError, match="Configura la variable de entorno URL"):
        extraccion.extraer_datos()


def test_variables_db_convierte_puerto_a_entero(monkeypatch):
    valores = {
        "USERNAME_DB": "usuario",
        "PASSWORD_DB": "secreto",
        "HOST_DB": "localhost",
        "PORT_DB": "5432",
        "NAME_DB": "transporte",
    }
    for clave, valor in valores.items():
        monkeypatch.setenv(clave, valor)

    assert carga._obtener_variables_db() == {
        "user": "usuario",
        "password": "secreto",
        "host": "localhost",
        "port": 5432,
        "dbname": "transporte",
    }


def test_variables_db_informa_variables_faltantes(monkeypatch):
    monkeypatch.setattr(carga, "load_dotenv", lambda: None)

    for clave in (
        "USERNAME_DB", "PASSWORD_DB", "HOST_DB", "PORT_DB", "NAME_DB"
    ):
        monkeypatch.delenv(clave, raising=False)

    with pytest.raises(ValueError, match="Faltan variables de entorno"):
        carga._obtener_variables_db()


def test_carga_pasajeros_falla_si_faltan_columnas(monkeypatch):
    monkeypatch.setattr(carga, "_obtener_variables_db", lambda: {})
    monkeypatch.setattr(
        carga, "_obtener_nombre_tabla", lambda _: "pasajeros"
    )
    entrada = pd.DataFrame({"zona_entrada": ["A"]})

    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        carga.cargar_datos_pasajeros(entrada)


def test_carga_tarifas_falla_si_faltan_columnas():
    entrada = pd.DataFrame({"Año": [2025]})

    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        carga.cargar_tarifas_viajes(entrada)


def test_orquestador_ejecuta_etapas_en_orden(monkeypatch):
    llamadas = []
    pasajeros = pd.DataFrame({"pasajeros": [1]})
    tarifas = pd.DataFrame({"tarifa": [2]})
    pasajeros_limpios = pd.DataFrame({"pasajeros": [3]})
    tarifas_limpias = pd.DataFrame({"tarifa": [4]})

    monkeypatch.setattr(
        orquestador, "extraer_datos",
        lambda: llamadas.append("extraer_pasajeros") or pasajeros,
    )
    monkeypatch.setattr(
        orquestador, "extraer_tarifas_barik",
        lambda: llamadas.append("extraer_tarifas") or tarifas,
    )
    monkeypatch.setattr(
        orquestador, "limpiar_datos_pasajeros",
        lambda df: llamadas.append("limpiar_pasajeros") or pasajeros_limpios,
    )
    monkeypatch.setattr(
        orquestador, "limpiar_tarifas_barik",
        lambda df: llamadas.append("limpiar_tarifas") or tarifas_limpias,
    )
    monkeypatch.setattr(
        orquestador, "cargar_datos_pasajeros",
        lambda df: llamadas.append("cargar_pasajeros") or df,
    )
    monkeypatch.setattr(
        orquestador, "cargar_tarifas_viajes",
        lambda df: llamadas.append("cargar_tarifas") or df,
    )

    resultado = orquestador.main()

    assert llamadas == [
        "extraer_pasajeros",
        "extraer_tarifas",
        "limpiar_pasajeros",
        "limpiar_tarifas",
        "cargar_pasajeros",
        "cargar_tarifas",
    ]
    assert resultado[0] is pasajeros_limpios
    assert resultado[1] is tarifas_limpias


def test_orquestador_no_continua_si_falla_extraccion(monkeypatch):
    llamadas = []

    def extraer_con_error():
        llamadas.append("extraccion")
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(orquestador, "extraer_datos", extraer_con_error)

    with pytest.raises(RuntimeError, match="fallo simulado"):
        orquestador.main()

    assert llamadas == ["extraccion"]