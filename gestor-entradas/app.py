import mysql.connector
import stripe
from flask import Flask, jsonify, render_template, request, redirect, session, abort, flash, send_file
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import qrcode
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
import secrets


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.lib.colors import HexColor
from io import BytesIO
import base64
import os


dias = ["Lun","Mar","Mie","Jue","Vie","Sab","Dom"]
meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

stripe.api_key = 'sk_test_51Mt8uiFnk6RDVw2rYcM4AwES8RJUnVx01mSke2JEey3wT2TrrJM8W1dU2bTE1YTJmp9X4EB8GvXkYhMd1A88HCgw00KwVOcSnx'




# The default folder name should be "templates" else need to mention custom folder name
app = Flask(__name__, template_folder='templateFiles', static_folder='staticFiles')
app.secret_key = secrets.token_hex(16)


@app.route('/descargar/<qr_string_path>', methods=['POST', 'GET'])
def descargar_pdf(qr_string_path):
    # Obtener la ruta completa del archivo PDF en el servidor
    pdf_path = os.path.join('staticFiles/pdf/', qr_string_path)

    # Verificar si el archivo PDF existe en el servidor
    if os.path.exists(pdf_path):
        # Enviar el archivo PDF como una descarga
        return send_file(pdf_path, as_attachment=True)
    else:
        # Retornar un mensaje de error si el archivo no existe
        return "El archivo PDF no fue encontrado en el servidor", 404



@app.route('/pruebacuenta')
def crear_cuenta_pruevas():
    stripe.Account.create(
  type="express",
  country="ES",
  capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}},
)
    return "done"


@app.route('/pdf')
def prueba_pdf():
    qr_string = "j73s83jd"
    evento = {"nombre": "Evento de Prueba", "fecha": "00_00_00", "hora": "00.00.00"}
    generar_pdf("Markel", "Ramiro Vaquero", qr_string, evento)
    pdf_url = f'https://wippass.com/staticFiles/pdf/ticket_{qr_string}.pdf'
    return redirect(pdf_url)



def generar_pdf(nombre, apellidos, qr_string, evento):

    # Crear un lienzo de PDF en el BytesIO
    c = canvas.Canvas(f'staticFiles/pdf/{qr_string}.pdf', pagesize=letter)

    # Definir un color de fondo oscuro
    background_color = HexColor('#ebeffa')

    # Agregar un rectángulo con el color de fondo
    c.setFillColor(background_color)
    c.rect(0, 0, letter[0], letter[1], fill=True)

    # Agregar imagen de QR al PDF centrado
    qr_code = QrCodeWidget(qr_string)
    qr_code_barcode = Drawing()
    qr_code_barcode.add(qr_code)
    qr_code_barcode.scale(5, 5)
    qr_code_barcode.wrapOn(c, 20 * mm, 20 * mm)
    qr_code_barcode.drawOn(c, 30 * mm, 30 * mm)

    # Agregar texto en el centro del PDF
    c.setFillColor(HexColor('#2d2d2d'))
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(110 * mm, 260 * mm, f"{evento['nombre']}")
    c.setFont("Helvetica", 30)
    c.drawCentredString(110 * mm, 35 * mm, f"{qr_string}")
    c.setFont("Helvetica", 20)
    c.drawCentredString(110 * mm, 240 * mm, f"Fecha: {evento['fecha']} a las {evento['hora']}")
    c.drawCentredString(110 * mm, 220 * mm, f"Asistente: {nombre} {apellidos}")

    # Guardar el PDF
    c.save()
#funcion para conectarme a mi base de datos
def conectar_db():
   conexion = mysql.connector.connect(
        user="admin",
        password="MramiroVa2002",
        host="gestor-de-entradas-pruebas.cllo4ks18szd.us-east-1.rds.amazonaws.com",
        database="myapp"
   )
   return conexion


def obtener_discotecas():
   discotecas = []
   try:
      conexion = conectar_db()
      cursor = conexion.cursor()
      consulta = f"""SELECT * FROM Discoteca"""
      cursor.execute(consulta)
      for (id, nombre, lugar, aforo, desc) in cursor:
         discotecas.append({'id':id,'nombre':nombre,'lugar':lugar,'aforo':aforo,'descripcion':desc})
      # Cerramos el cursor y la conexión a la base de datos
      cursor.close()
      conexion.close()
   except mysql.connector.Error as error:
      return -1
   return discotecas


from passlib.apps import custom_app_context as pwd_context
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        password = request.form['password']
        conpassword = request.form['conpassword']
        email = request.form['email']
        role = request.form['owners']
        try:
            conexion = conectar_db()
            cursor = conexion.cursor()
            consulta = f"""SELECT email FROM user where email='{email}'"""
            cursor.execute(consulta)

            # user = User.query.filter_by(email=email).first()
            if cursor is None:
                if password == conpassword :
                    password_hash = pwd_context.encrypt(password)
                    # user = User(firstname=firstname,lastname=lastname,password=password_hash,email=email,role=role)
                    user = f"INSERT INTO user (firstname, lastname, email, password, role) VALUES('{firstname}', '{lastname}', '{password_hash}', '{email}', '{role}')"
                    cursor.execute(user)
                    conexion.commit()
                    return "User registered successfully"
                else:
                    return "Your password and confirmation password do not match."
            else:
                return "Your email is already exists"
            cursor.close()
            conexion.close()    
        except mysql.connected.Error as error:
            print(f'Error al insertar: {error}')
            return error
            
    return render_template('index.html')


# Función para obtener los eventos de la discoteca
def obtener_eventos_disco(disco_nombre):
    eventos = []
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        # Consulta para obtener los eventos
        consulta = f"""SELECT e.id, e.id_disco, e.nombre, e.descripcion, e.fecha, e.edad
                    FROM Evento e JOIN Discoteca d ON e.id_disco = d.id
                    WHERE d.nombre = '{disco_nombre}'
                    ORDER BY e.fecha ASC;"""

        cursor.execute(consulta)
        for (id, id_disco, nombre, desc, fecha, edad) in cursor:
            d = dias[fecha.weekday()]
            n = str(fecha.day)
            m = meses[fecha.month -1]
            fecha_visual = d + ', ' + n + ' ' + m[:3]
            eventos.append({'id':id,'nombre':nombre,'descripcion':desc,'sala_nombre':disco_nombre, 'fecha':fecha,'edad': edad,  'fecha_visual':fecha_visual})
        # Cerramos el cursor y la conexión a la base de datos
        cursor.close()
        conexion.close()
    except mysql.connector.Error as error:
        return -1
    return eventos


def obtener_mapa(disco_id):
    map = None
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        # Consulta para obtener los eventos
        consulta = f"""SELECT queryString, place_id, cid
                    FROM Mapa
                    WHERE id = '{disco_id}'
                    ;"""

        cursor.execute(consulta)
        for (a, b, c) in cursor:
            map = {'queryString':a,'place_id':b,'cid':c}
        # Cerramos el cursor y la conexión a la base de datos
        cursor.close()
        conexion.close()
    except mysql.connector.Error as error:
        return map
    return map



# Función para obtener los eventos de la base de datos
def obtener_eventos():
    eventos = []
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        # Consulta para obtener los eventos
        consulta_eventos = "SELECT e.id AS id_evento, e.nombre AS nombre_evento, e.descripcion, d.nombre AS nombre_discoteca, e.fecha FROM Evento e JOIN Discoteca d ON e.id_disco = d.id ORDER BY e.fecha ASC;"
        cursor.execute(consulta_eventos)

        # Recorremos los resultados y los guardamos en una lista
        for (id, nombre, descripcion, sala_nombre, fecha) in cursor:
            eventos.append({'id': id, 'nombre': nombre, 'descripcion': descripcion, 'sala_nombre': sala_nombre, 'fecha': fecha})

        # Cerramos el cursor y la conexión a la base de datos
        cursor.close()
        conexion.close()
    except mysql.connector.Error as error:
        print(f"Error al obtener los eventos: {error}")
    return eventos

def obtener_rrpp(rrpp_id):
    rrpp = None
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        # Consulta para obtener el RRPP con el id especificado
        consulta = "SELECT nombre, apellido FROM RRPP WHERE id=%s"
        cursor.execute(consulta, (rrpp_id,))

        # Obtenemos el resultado y guardamos el nombre y apellido en un diccionario
        resultado = cursor.fetchone()
        if resultado:
            nombre, apellido = resultado
            rrpp = {'nombre': nombre, 'apellido': apellido, 'id':rrpp_id}

        # Cerramos el cursor y la conexión a la base de datos
        cursor.close()
        conexion.close()
    except mysql.connector.Error as error:
        print(f"Error al obtener el RRPP: {error}")
    return rrpp


def obtener_eventos_rrpp(rrpp_id):
    eventos_rrpp = []
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        # Consulta para obtener los eventos de un RRPP en particular
        consulta = "SELECT Evento.id, Evento.nombre, Evento.descripcion, Evento.fecha, Discoteca.nombre, Evento.edad FROM Evento INNER JOIN Discoteca ON Evento.id_disco=Discoteca.id INNER JOIN RRPP_Evento ON Evento.id=RRPP_Evento.evento_id WHERE RRPP_Evento.rrpp_id=%s  ORDER BY Evento.fecha ASC;"

        cursor.execute(consulta, (rrpp_id,))
        # Recorremos los resultados y los guardamos en una lista
        for (id, nombre, descripcion, fecha, disco_nombre, edad) in cursor:
            d = dias[fecha.weekday()]
            n = str(fecha.day)
            m = meses[fecha.month -1]
            fecha_visual = d + ', ' + n + ' ' + m[:3]
            eventos_rrpp.append({'id': id, 'nombre': nombre, 'descripcion': descripcion, 'fecha': fecha,'fecha_visual':fecha_visual, 'sala_nombre': disco_nombre, 'edad': edad})

        # Cerramos el cursor y la conexión a la base de datos
        cursor.close()
        conexion.close()
    except mysql.connector.Error as error:
        print(f"Error al obtener los eventos del RRPP {rrpp_id}: {error}")
    return eventos_rrpp


def obtener_disco(disco_nombre):
    discoteca = None
    try:
       conexion = conectar_db()
       cursor = conexion.cursor()
       consulta = "SELECT * FROM Discoteca WHERE nombre = %s;"

       cursor.execute(consulta, (disco_nombre,))

       for (id, nombre, lugar, aforo, desc) in cursor:
            discoteca = {'id':id, 'nombre':nombre, 'lugar':lugar, 'aforo':aforo, 'descripcion': desc}

       cursor.close()
       conexion.close()
       if not discoteca == None:
          return discoteca
       else:
          abort(404)
    except mysql.connector.Error as error:
       print(f"Error al obtener el disco {disco_nombre}")

       return -1



def obtener_discoteca(disco_id):
    discoteca = None
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()

        consulta = "SELECT * FROM Discoteca WHERE id = %s;"

        cursor.execute(consulta, (disco_id,))

        for (id, nombre, lugar, aforo, desc) in cursor:
            discoteca = {'id':id, 'nombre':nombre, 'lugar':lugar, 'aforo':aforo, 'descripcion': desc}

        cursor.close()
        conexion.close()

    except mysql.connector.Error as error:
        print(f"Error al obtener el disco {disco_id}")

    return discoteca



def obtener_evento(evento_id):
    evento = None
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        # Consulta para obtener las entradas de un evento en particulas
        consulta = "SELECT * FROM Evento WHERE id = %s;"

        cursor.execute(consulta, (evento_id,))

        for (id, disco, nombre, descripcion, aforo, fecha, hora, edad) in cursor:
            d = dias[fecha.weekday()]
            n = str(fecha.day)
            m = meses[fecha.month -1]
            fecha_visual = d + ', ' + n + ' ' + m[:3]
            evento = {'id':id,'disco':disco,'nombre':nombre,'descripcion':descripcion, 'fecha':fecha,'fecha_visual':fecha_visual, 'hora':hora, 'edad':edad}

        cursor.close()
        conexion.close()

    except mysql.connector.Error as error:
        print(f"Error al obtener el evento {evento_id}")
    print(evento)
    return evento

def obtener_entrada(entrada_id):
    entrada = None
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        # Consulta para obtener las entradas de un evento en particulas
        consulta = "SELECT * FROM Entrada WHERE id = %s;"

        cursor.execute(consulta, (entrada_id,))

        for (id, id_evento, tipo, precio, restantes) in cursor:
            entrada = {'id':id, 'id_evento': id_evento, 'tipo':tipo, 'precio':precio, 'restantes': restantes}

        cursor.close()
        conexion.close()

    except mysql.connector.Error as error:
        print(f"Error al obtener la entrada {entrada_id}")

    return entrada


def obtener_entradas(evento_id):
    entradas = []
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        # Consulta para obtener las entradas de un evento en particulas
        consulta = "SELECT * FROM Entrada WHERE id_evento = %s ORDER BY precio ASC;"

        cursor.execute(consulta, (evento_id,))

        for (id, id_evento, tipo, precio, restantes) in cursor:
            entradas.append({'id':id,'id_evento':id_evento,'tipo':tipo,'precio':precio, 'restantes':restantes})

        cursor.close()
        conexion.close()

    except mysql.connector.Error as error:
        print(f"Error al obtener las Entradas del Evento {evento_id}: {error}")

    return entradas


#funcion para añadir evento
def guardar_evento(disco_id, nombre, descripcion, aforo, fecha, hora):
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()

        # insertar datos de evento
        consulta= "INSERT INTO Evento (id_disco, nombre, descripcion, aforo, fecha, hora) VALUES (%s, %s, %s, %s, %s, %s)"
        valores = (disco_id, nombre, descripcion, aforo, fecha, hora)
        cursor.execute(consulta, valores)

        evento_id = cursor.lastrowid

        conexion.commit()
        cursor.close()
        conexion.close()

        return evento_id

    except mysql.connector.Error as error:
        print(f'Error al insertar: {error}')
        return None

#funcion para añadir entrada
def guardar_entrada(id_evento, tipo, precio, restantes):
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()

        # insertar datos de evento
        consulta= "INSERT INTO Entrada (id_evento, tipo, precio, restantes) VALUES (%s, %s, %s, %s)"
        valores = (id_evento, tipo, precio, restantes)
        cursor.execute(consulta, valores)

        conexion.commit()
        cursor.close()
        conexion.close()

    except mysql.connector.Error as error:
        print(f'Error al insertar: {error}')





#funcion para añadir nueva venta
def guardar_venta_y_cliente(nombre, apellidos, fecha_nacimiento, correo, sexo, cifrado, evento_id, entrada_id, rrpp_id):
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()

        # Consulta a la tabla Entrada para obtener el valor del atributo restantes
        consulta_entrada = "SELECT restantes FROM Entrada WHERE id = %s"
        valores_entrada = (entrada_id,)
        cursor.execute(consulta_entrada, valores_entrada)
        restantes = cursor.fetchone()[0]


        if restantes > 0:

            # Primero, insertar los datos del cliente
            consulta_cliente = "INSERT INTO Cliente (nombre, apellidos, correo, sexo, fecha_nacimiento) VALUES (%s, %s, %s, %s, %s)"
            valores_cliente = (nombre, apellidos, correo, sexo, fecha_nacimiento)
            cursor.execute(consulta_cliente, valores_cliente)

            # Obtener el ID del cliente insertado
            cliente_id = cursor.lastrowid

            if not rrpp_id == "None":
               # Segundo, insertar los datos de la venta
               consulta_venta = "INSERT INTO Venta (id_cliente, id_entrada, id_evento, qr, id_rrpp) VALUES (%s, %s, %s, %s, %s)"
               valores_venta = (cliente_id, entrada_id, evento_id, cifrado, rrpp_id)
               cursor.execute(consulta_venta, valores_venta)

            else:
               # Segundo, insertar los datos de la venta
               consulta_venta = "INSERT INTO Venta (id_cliente, id_entrada, id_evento, qr) VALUES (%s, %s, %s, %s)"
               valores_venta = (cliente_id, entrada_id, evento_id, cifrado)
               cursor.execute(consulta_venta, valores_venta)

            # Agregar el ID de la venta creada a la lista de IDs
            id_venta = cursor.lastrowid

            conexion.commit()

        else:
            print("No hay entradas disponibles")

        cursor.close()
        conexion.close()
        return id_venta
    except mysql.connector.Error as error:
        print(f'Error al insertar: {error}')
        return error

def enviar_correo(correo, qr_string, nombre, apellidos, rrpp_id, evento):

    generar_pdf(nombre, apellidos, qr_string, evento)
    pdf_url = 'https://wippass.com/descargar/' + qr_string + '.pdf'


    # generar el codigo QR a partir del mensaje cifrado
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=4,
    )
    qr.add_data(qr_string)
    qr.make(fit=False)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # guardar el codigo QR como una imagen
    qr_img.save(f'staticFiles/imagenes/qr/qr_code_{qr_string}.png')


    rrpp_nombre = "No"
    if not rrpp_id == "None":
       rrpp = obtener_rrpp(rrpp_id)
       rrpp_nombre = rrpp['nombre'] + ' ' + rrpp['apellido']
    # Datos del correo electrónico
    email_from = "Wippass <ticket@wippass.com>"
    email_to =correo
    email_subject = "TU ENTRADA"
    html = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Tu Entrada</title>
  </head>
  <body style="background-color: #393939;">
    <table width="100%" cellspacing="0" cellpadding="0" border="0">
      <tr>
        <td align="center">
          <table width="600" cellspacing="0" cellpadding="0" border="0">
            <tr>
              <td align="center" style="padding: 50px;">
                <img src="https://wippass.com/staticFiles/imagenes/wippass_logo.png" alt="Logo" width="150" heigth="100">
              </td>
            </tr>
            <tr>
              <td align="center" style="padding: 50px; background-color: #DFDFDF;">
                <table width="500" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td align="left" style="font-family: Arial, sans-serif; font-size: 18px; color: #000000; line-height: 24px;">
                      <p><strong>Tu Entrada:</strong></p>
                      <p><strong>Evento:</strong> {evento['nombre']}</p>
                      <p><strong>Fecha: </strong> {evento['fecha']} a las {evento['hora']}</p>
                      <p><strong>Cliente:</strong> {nombre} {apellidos}</p>
                      <p><strong>RRPP:</strong> {rrpp_nombre}</p>
                    </td>
                  </tr>
                </table>
                <table align="center">
                 <tr>
                  <td>
                   <p><img src="https://wippass.com/staticFiles/imagenes/qr/qr_code_{qr_string}.png" alt="QR code" width="200"></p>
                  </td>
                 </tr>
              </table>
              <table align="center">
               <tr>
                <td>
                 <a href="{pdf_url}">
                   <button style="background-color: #1b75ff; border: none; border-radius: 10px; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">
                     DESCARGAR QR
                   </button>
                 </a>
                </td>
               </tr>
              </table>
              </td>
            </tr>
            <tr>
              <td align="center" style="padding: 50px; font-family: Arial, sans-serif; font-size: 12px; color: #FFFFFF;">
                <p>Este correo electrónico ha sido generado automáticamente. Por favor no responda a este mensaje.</p>
                <p>© 2023 Wippass</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
    """
    # Crear el mensaje
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = email_subject


    email_body = MIMEText(html, 'html')

    msg.attach(email_body)

    # Enviar el correo electrónico
    smtp_server = "smtp.ionos.es"
    smtp_port = 587
    smtp_username = "ticket@wippass.com"
    smtp_password = "DUz66tXd3001"

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(email_from, email_to, msg.as_string())


def existe(qr_data, evento_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    consulta = f"""
                   SELECT COUNT(*) as existe
                   FROM Venta v
                   JOIN Entrada e ON v.id_entrada = e.id
                   WHERE e.id_evento = {evento_id}
                   AND v.qr = '{qr_data}'
                   """

    cursor.execute(consulta)
    resultado = cursor.fetchone()
    existe = resultado[0]

    if not existe:
        cursor.close()
        conexion.close()
        return {'entrar':0, 'arg':"QR INCORRECTO"}


    else:

        consulta = f"""
                   SELECT validated
                   FROM Venta v
                   WHERE qr = '{qr_data}';
                """

        cursor.execute(consulta)
        resultado = cursor.fetchone()
        validated = resultado[0]

        if validated: # el QR ya ha sido escaneado
            cursor.close()
            conexion.close()
            return {'entrar':0, 'arg':"QR ESCANEADO ANTERIORMENTE"}


        else:
            consulta = f"""
                   SELECT nombre
                   FROM Venta v JOIN Cliente c ON v.id_cliente = c.id
                   WHERE v.qr = '{qr_data}';
                """
            cursor.execute(consulta)
            resultado = cursor.fetchone()
            nombre = resultado[0]

            consulta = f"""
                   UPDATE Venta SET validated = 1 WHERE qr = '{qr_data}';
                  """
            cursor.execute(consulta)
            conexion.commit()

            cursor.close()
            conexion.close()
            return {'entrar':1, 'arg':nombre}


def obtener_clientes_json(evento_id):
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        consulta = f'''
                   SELECT Cliente.*, Venta.validated FROM Cliente INNER JOIN Venta ON Cliente.id = Venta.id_cliente WHERE Venta.id_evento = {evento_id};
                   '''
        cursor.execute(consulta)
        clientes = cursor.fetchall()
        cursor.close()
        conexion.close()
        return jsonify(clientes)
    except mysql.connector.Error as error:
        print(f'Error al insertar: {error}')
        return error

def obtener_clientes(evento_id):
    clientes = []
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        consulta = f'''
                   SELECT Cliente.*, Venta.validated FROM Cliente INNER JOIN Venta ON Cliente.id = Venta.id_cliente WHERE Venta.id_evento = {evento_id};
                   '''
        cursor.execute(consulta)
        for (nombre, apellido, correo, sexo, fecha_nac, id, val) in cursor:
           clientes.append({'nombre':nombre,'apellido':apellido,'correo':correo,'sexo':sexo,'fecha_nacimiento':fecha_nac,'id':id,'val':val})
        cursor.close()
        conexion.close()
        return clientes
    except mysql.connector.Error as error:
        print(f'Error al insertar: {error}')
        return error



def obtener_cifrado(nombre, apellido, correo, evento_id, entrada_id):
    # generar clave privada
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # generar clave pública a partir de la clave privada
    public_key = private_key.public_key()

    # cifrar el mensaje
    clave_personal = 'laputivuelta'
    mensaje = f'{nombre}{apellido}{correo}{evento_id}{entrada_id}{clave_personal}'
    mensaje_codificado = mensaje.encode('utf-8')
    cifrado = public_key.encrypt(
        mensaje_codificado,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    cifrado = cifrado.hex() # pasar de bytes a hex

    cifrado_corto = cifrado[:10] #coger los ultimos 10 caracteres solo

    # descifrar el mensaje
    descifrado = private_key.decrypt(
        bytes.fromhex(cifrado),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    mensaje_descifrado = descifrado.decode('utf-8')
    return cifrado_corto

def guardar_transaccion(venta_ids, cantidad):
    print(cantidad)
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        # Crear la transacción
        cursor.execute("INSERT INTO Transaccion (cantidad, fecha) VALUES (%s, NOW())", (cantidad,))
        transaccion_id = cursor.lastrowid

        # Relacionar la transacción con cada venta correspondiente
        for venta_id in venta_ids:
            cursor.execute("INSERT INTO Venta_Transaccion (id_venta, id_transaccion) VALUES (%s, %s)", (venta_id, transaccion_id))

        # Confirmar los cambios en la base de datos
        conexion.commit()

    except Exception as e:
        print(f"Error al guardar la transacción: {e}")
        conexion.rollback()

    finally:
        cursor.close()
        conexion.close()



@app.route('/')
def index():
    discotecas = obtener_discotecas()
    return render_template('index.html', discotecas=discotecas)

# Ruta para mostrar la página de eventos
@app.route('/<disco_nombre>')
def mostrar_eventos(disco_nombre):
    discoteca = obtener_disco(disco_nombre)
    if not discoteca==-1:
       # Obtenemos los eventos de la discoteca
       eventos = obtener_eventos_disco(disco_nombre)
       map = obtener_mapa(discoteca['id'])
       return render_template('eventos_discoteca.html', eventos=eventos, disco_nombre=disco_nombre, discoteca=discoteca, rrpp=None, map=map)

    else:
       abort(404)




@app.route('/<disco_nombre>/<disco_pass>')
def mostrar_clientes_evento(disco_nombre, disco_pass):
    discoteca = obtener_disco(disco_nombre)
    if not discoteca==-1 and True:
        # Obtenemos los eventos de la discoteca
        eventos = obtener_eventos_disco(disco_nombre)

        # Verificar si un evento fue seleccionado en el formulario
        evento_id = request.args.get('eventos')
        clientes = []
        if evento_id:
            clientes = obtener_clientes(evento_id)

        return render_template('eventos_y_clientes.html', eventos=eventos, discoteca=discoteca, clientes=clientes)

    else:
        abort(404)


@app.route('/clientes/<disco_nombre>/<disco_pass>/<evento_id>')
def obtener_clientess(disco_nombre, disco_pass, evento_id):
    # Obtener la lista de clientes del evento
    clientes = obtener_clientes(evento_id)
    return render_template("clientes_evento.html", clientes=clientes, total_clientes = len(clientes))




@app.route('/evento/<int:evento_id>')
def entradas_evento(evento_id):
    entradas = obtener_entradas(evento_id)
    evento = obtener_evento(evento_id)
    discoteca = obtener_discoteca(evento['disco'])
    rrpp_id = request.args['rrpp']
    return render_template('entradas_evento.html', entradas=entradas, evento=evento, discoteca=discoteca, rrpp_id = rrpp_id)


@app.route('/rrpp/<rrpp_id>')
def rrpp_eventos(rrpp_id):
    rrpp = obtener_rrpp(rrpp_id) # función para obtener el nombre y apellido del RRPP
    eventos_rrpp = obtener_eventos_rrpp(rrpp_id) # función para obtener eventos de un RRPP específico
    return render_template('eventos_rrpp.html', rrpp=rrpp, eventos=eventos_rrpp)


@app.route('/evento/<int:evento_id>/<int:entrada_id>', methods = ['GET'])
def ingresar_datos(evento_id, entrada_id):
    evento = obtener_evento(evento_id)
    entrada = obtener_entrada(entrada_id)
    #obtener la entrada
    entrada = obtener_entrada(entrada_id)
    restantes = entrada['restantes']
    arg = request.args['rrpp']
    index = arg.find(',')
    print(f"index: {index}")
    rrpp_id = arg[:index]
    cantidad = int(arg[index+1:])

    if restantes < cantidad:
        return render_template('entrada_agotada.html')

    unidad = int(entrada['precio'])
    gg = round(0.85-(cantidad*0.024) + unidad*0.016, 2)

    total = round((gg+unidad)*cantidad, 2)

    return render_template('datos_cliente.html', evento=evento, entrada=entrada, cantidad=cantidad, rrpp_id=rrpp_id, unidad=unidad, gg=gg, total=total)


@app.route('/evento/<int:evento_id>/<int:entrada_id>', methods=['POST'])
def procesar_formulario(evento_id, entrada_id):
    arg = request.args['rrpp']
    index = arg.find(',')
    print(f"index: {index}")
    rrpp_id = arg[:index]
    cantidad = int(arg[index+1:])

    #comprobar si siguen quedando (cantidad) entradas
    evento = obtener_evento(evento_id)
    entrada = obtener_entrada(entrada_id)
    if cantidad>entrada['restantes']:
       return render_template('entrada_agotada.html')

    # Obtener los datos del formulario
    clientes = []
    for i in range(cantidad):
        nombre = request.form[f'nombre{i}']
        apellido = request.form[f'apellido{i}']
        fecha_nacimiento = request.form[f'fecha_nacimiento{i}']
        correo = request.form[f'correo{i}']
        sexo = request.form[f'sexo{i}']

        # Guardar los datos en una lista
        clientes.append({
            'nombre': nombre,
            'apellido': apellido,
            'fecha_nacimiento': fecha_nacimiento,
            'correo': correo,
            'sexo': sexo,
        })

    # Guardar los datos en variables de sesión
    session['clientes'] = clientes
    session['rrpp_id'] = rrpp_id
    session['evento_id'] = evento_id
    session['entrada_id'] = entrada_id
    session['fecha_nacimiento'] = fecha_nacimiento
    # Crear el objeto de precio para Stripe
    precio_unitario = int(entrada['precio'])
    gg = round(0.85 - cantidad * 0.024 + precio_unitario * 0.016, 2) # gasto de gestion por entrada
    precio_total = (gg + precio_unitario) * cantidad

    precio = stripe.Price.create(
        unit_amount=int(precio_total * 100),
        currency='eur',
        product_data={
            'name': evento['nombre'] + ' - ' + entrada['tipo'] + ' - ' + str(cantidad)
        }
    )

    # return redirect('https://wippass.com/compra-confirmada')
    # Crear el objeto de checkout session para Stripe
    checkout_session = stripe.checkout.Session.create(
        line_items=[{
            'price': precio.id,
            'quantity': 1
        }],
        mode='payment',
        success_url='https://wippass.com/compra-confirmada',
        cancel_url='https://wippass.com/compra-cancelada'
    )

    # Redireccionar al usuario a la página de pago de Stripe
    return redirect(checkout_session.url, code=303)

# Ruta para añadir eventos
@app.route('/add_evento', methods=['GET'])
def ingresar_evento_privilegio():
    discotecas = obtener_discotecas()
    return render_template('insertar_eventos_privilegio.html', discotecas=discotecas)


@app.route('/add_evento', methods=['POST'])
def procesar_nuevo_evento_privilegio():
    disco_id = request.form['disco_id']
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    fecha = request.form['fecha']
    aforo = request.form['aforo']
    hora = request.form['hora']

    evento_id = guardar_evento(disco_id, nombre, descripcion, aforo, fecha, hora)

    # manejar la imagen cargada por el usuario
    imagen = request.files['imagen']
    ruta_imagen = f"staticFiles/imagenes/eventos/evento{evento_id}.png"
    imagen.save(ruta_imagen)

    return render_template('insertar_entradas_privilegio.html', evento_id=evento_id)

# Ruta para añadir entradas
@app.route('/add_entrada', methods=['GET'])
def ingresar_entrada_privilegio():
    return render_template('insertar_entradas_privilegio.html')


@app.route('/add_entrada', methods=['POST'])
def procesar_nueva_entrada_privilegio():
    id_evento = request.form['evento_id']
    tipo = request.form['tipo']
    precio = request.form['precio']
    restantes = request.form['restantes']
    guardar_entrada(id_evento, tipo, precio, restantes)
    flash('Entrada añadida correctamente', 'success')
    return render_template('insertar_entradas_privilegio.html', evento_id=id_evento)


@app.route('/compra-cancelada', methods=['GET'])
def compra_cancelada():
    session.pop('clientes', None)
    session.pop('rrpp_id', None)
    session.pop('evento_id', None)
    session.pop('entrada_id', None)
    return render_template("compra_cancelada.html")


@app.route('/compra-confirmada', methods=['GET', 'POST'])
def compra_confirmada():
    # Obtener los datos del formulario de la variable de sesión
    clientes = session.get('clientes', [])
    rrpp_id = session.get('rrpp_id')
    evento_id = session.get('evento_id')
    entrada_id = session.get('entrada_id')
    evento = obtener_evento(evento_id)
    venta_ids = []
   # cifrado_corto = "aghi6y3gw2"
   # evento_id = 21
   # entrada_id = 45
   # rrpp_id = "None"
   # clientes = [{    'nombre': 'Juan',    'apellido': 'Pérez',    'fecha_nacimiento': '1990-01-01',    'correo': 'gernika2002@gmail.com',    'sexo': 'M'}]
   # evento = {'id':21, 'nombre':"La fiesta", 'fecha':"fecha",'hora':"hora"}
    # Guardar la venta y los clientes en la base de datos
    for cliente in clientes:
        cifrado_corto = obtener_cifrado(cliente['nombre'], cliente['apellido'], cliente['correo'], evento_id, entrada_id)
        venta_ids.append(guardar_venta_y_cliente(cliente['nombre'], cliente['apellido'], cliente['fecha_nacimiento'], cliente['correo'], cliente['sexo'], cifrado_corto, evento_id, entrada_id, rrpp_id))
        enviar_correo(cliente['correo'], cifrado_corto, cliente['nombre'], cliente['apellido'], rrpp_id, evento)


    guardar_transaccion(venta_ids, len(venta_ids))
    return render_template("compra_confirmada.html")


# Ruta para verificar QR
@app.route('/check_qr', methods=['GET'])
def check_qr():
    qr_data = request.args['data']
    evento_id = request.args['evento_id']
    resultado = existe(qr_data, evento_id)  #{estado:, arg:}
    return resultado


# FUNCION PARA LA APP MOVIL
@app.route('/mostrar_clientes', methods=['GET'])
def mostrar_clientes():
    evento_id = request.args['evento_id']
    clientes = obtener_clientes_json(evento_id)
    return clientes

@app.route('/terminos-y-condiciones')
def terminos_condiciones():
    return render_template('terminos_condiciones.html')



if __name__ == "__main__":
    app.run(debug=True)


