--Pasajeros tabla
CREATE TABLE IF NOT EXISTS trans_viajes_bizkaia (
    zona_entrada INTEGER,
    zona_salida INTEGER,
    Modo VARCHAR(50),
    pasajeros INTEGER,
    fecha_hora TIMESTAMP,
    PRIMARY KEY (fecha_hora, zona_entrada, zona_salida, Modo, pasajeros)
);

SELECT * FROM trans_viajes_bizkaia;

--Fechas de extraccion de datos de tarifas
SELECT 
	MIN(fecha_hora),--2022
	MAX(fecha_hora) --2025
FROM trans_viajes_bizkaia;

--Contar numeros de registros de la tabla y que coincidan con los de la carga en la terminal
SELECT 
	COUNT(*)
FROM trans_viajes_bizkaia;


--Tarifas tabla
CREATE TABLE IF NOT EXISTS tarifas_viajes (
    Año SMALLINT,
	Modo VARCHAR(50),
    zona_1 FLOAT,
    zona_2 FLOAT,
	zona_3 FLOAT,
    zona_4 FLOAT,
    zona_5 FLOAT
);

SELECT * FROM tarifas_viajes;