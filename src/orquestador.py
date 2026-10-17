try:
    from .extraccion import extraer_datos, extraer_tarifas_barik
    from .limpieza import limpiar_datos_pasajeros, limpiar_tarifas_barik
    from .carga import cargar_datos_pasajeros, cargar_tarifas_viajes
except ImportError:
    from extraccion import extraer_datos, extraer_tarifas_barik
    from limpieza import limpiar_datos_pasajeros, limpiar_tarifas_barik
    from carga import cargar_datos_pasajeros, cargar_tarifas_viajes
import time

# Función principal
def main():
    #Inicializar tiempo de ejecución
    inicio = time.time()

    #EXTRACCION DE DATOS
    df_pasajeros = extraer_datos()
    df_tarifas = extraer_tarifas_barik()
    Extraccion = time.time() - inicio
    print(f"Proceso de EXTRACCIóN de datos terminado. En {Extraccion:.2f} segundos")

    #LIMPIEZA DE DATOS
    df_limpio_pasajeros = limpiar_datos_pasajeros(df_pasajeros)
    print(f"\nProceso completado para pasajeros. Filas limpias: {len(df_limpio_pasajeros):,}")
    print(f"\nColumnas limpias para pasajeros: {len(df_limpio_pasajeros.columns)}")

    df_limpio_tarifas = limpiar_tarifas_barik(df_tarifas)
    print(f"\nProceso completado para tarifas. Filas limpias: {len(df_limpio_tarifas):,}")
    print(f"\nColumnas limpias para tarifas: {len(df_limpio_tarifas.columns)}")

    limpieza = time.time() - Extraccion
    print(f"Proceso de LIMPIEZA de datos terminado. En {limpieza:.2f} segundos")

    #CARGA DE DATOS
    df_cargado_pasajeros = cargar_datos_pasajeros(df_limpio_pasajeros)
    df_cargado_tarifas = cargar_tarifas_viajes(df_limpio_tarifas)

    carga = time.time() - limpieza
    print(f"Proceso de CARGA de datos terminado. En {carga:.2f} segundos")

    #Finalización de la ETL
    duracion = time.time() - inicio
    print(f"Duración del ETL: {duracion:.2f} segundos")

    return df_cargado_pasajeros, df_cargado_tarifas


if __name__ == "__main__":
    df_final = main()
