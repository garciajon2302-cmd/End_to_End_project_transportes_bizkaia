--Pasajeros tabla
CREATE TABLE IF NOT EXISTS trans_viajes_bizkaia (
    zona_entrada INTEGER,
    zona_salida INTEGER,
    Modo VARCHAR(50),
    pasajeros INTEGER,
    fecha_hora TIMESTAMP,
    PRIMARY KEY (fecha_hora, zona_entrada, zona_salida, Modo, pasajeros)
);

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

