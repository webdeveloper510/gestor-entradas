import mysql.connector

config = {
    'host': 'gestor-de-entradas-pruebas.cllo4ks18szd.us-east-1.rds.amazonaws.com',
    'database':'myapp',
    'user': 'admin',
    'password': 'MramiroVa2002'
}


cnx = mysql.connector.connect(**config)

# Obtener un cursor
cursor = cnx.cursor()

# Ejecutar la consulta para listar las bases de datos
cursor.execute('''INSERT INTO Sala (nombre, lugar, aforo) VALUES ('Sala de prueba', 'Bilbao', 100);
''')

for table in cursor:
   print(table)


# Cerrar el cursor y la conexión
cursor.close()
cnx.commit()
cnx.close()
