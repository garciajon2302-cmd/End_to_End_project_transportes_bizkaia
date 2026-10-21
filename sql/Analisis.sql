SELECT * FROM trans_viajes_bizkaia;

--Fechas de extraccion de datos de tarifas
SELECT 
	MIN(fecha_hora),--2022
	MAX(fecha_hora) --2025
FROM trans_viajes_bizkaia;

--Contar numeros de registros de la tabla y que coincidan con los de la carga en la terminal
SELECT 
	COUNT(*)
FROM trans_viajes_bizkaia; --1.885.414 registros

--Tarifas del web scraping

SELECT * FROM tarifas_viajes;