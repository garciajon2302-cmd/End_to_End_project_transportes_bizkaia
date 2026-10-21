WITH tabla_maestra AS(
SELECT
    pas.*,
    CASE GREATEST(pas.zona_entrada, pas.zona_salida)
        WHEN 1 THEN tar.zona_1
        WHEN 2 THEN tar.zona_2
        WHEN 3 THEN tar.zona_3
        WHEN 4 THEN tar.zona_4
        WHEN 5 THEN tar.zona_5
    END AS precio_billete
FROM trans_viajes_bizkaia pas
JOIN tarifas_viajes tar
    ON tar.año = EXTRACT(YEAR FROM pas.fecha_hora)::integer
    AND tar.modo = pas.modo
)