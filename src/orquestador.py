try:
    from .extraccion import extraer_datos
    from .limpieza import limpiar_datos
    from .carga import cargar_datos
except ImportError:
    from extraccion import extraer_datos
    from limpieza import limpiar_datos
    from carga import cargar_datos
import time

def main():
    inicio = time.time()
    df_extraido = extraer_datos()
    df_limpio = limpiar_datos(df_extraido)

    print(f"\nProceso completado. Filas limpias: {len(df_limpio):,}")
    print(f"\nColumnas limpias: {len(df_limpio.columns)}")

    df_cargado = cargar_datos(df_limpio)
    duracion = time.time() - inicio
    print(f"Duración: {duracion:.2f} segundos")
    return df_limpio


if __name__ == "__main__":
    df_final = main()
