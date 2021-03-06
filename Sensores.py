#! /usr/bin/python
import time
import bluetooth 
import atexit
import time 
import select
import os
import sys
import string
import re
import signal
import Tkinter 
import tkMessageBox

NOMBRE = "Sensores"				# Nombre que aparecen en la ventana
ALTO = "400"					# Numero de pixeles que tendra de alto la ventana
ANCHO = "500"					# Numero de pixeles que tendra de ancho la ventana

SEPARADOR = '|'					# Simbolo que permite identificar entre los datos que llegan de la arduino donde empieza y termina cada linea
LIMIT = ","						# Simbolo que separa los datos que vienen en una linea
CANT_LINEAS = 5					# Cantidad de lineas que se deben acumular para poder guardar en el archivo de datos (si se guarda de una en una es mas lento el programa)
CANT_MENSAJES = 15				# Cantidad de mensaje que se guardaran en el historial de la aplicacion
RUTA = ""						# Carpeta donde se guardara el archivo, dejar "" para guardar en la misma carpeta del programa
CARPETA_DATOS = "DatosArduino"	# Nombre de la carpeta que guardara los datos
LIMPIAR = set(string.printable)	# Se usa para quitar los caracteres que llegan con error de la arduino
BOTONES = {	"Bomba On": '5', 	# ["Nombre funcion"] : 'numero', el nombre de funcion puede ser cualquiera pero el numero debe coincidir con el numero del comando en arduino 
			"Bomba Off": '6', 
			"Valvula1 On": '7', 
			"Valvula1 Off": '8',			
			"Valvula2 On": '9', 
			"Valvula2 Off": '10', 
			"Valvula3 On": '11', 
			"Valvula3 Off": '12' }

leido = ""  							# Variable que va guardando todo lo que se recibe de la arduino
anteriorFecha = ""						# Variable que se usa para verificar la fecha de los archivos de los datos y poder separar los datos de diferentes fechas en diferentes archivos
mensaje = None							# Variable que tendra los mensajes que se mostraran en la aplicacion
historial = []							# Historial de mensajes de la aplicacion 
lineas = []								# Variable que va acumulando las lineas que se guardan en el archivo de datos
arduino = None							# Se debe iniciar desde aca la variable que se asocia con la conexion bluetooth de arduino
ventana = None
mensajeVentana = None


def imprimir(texto):				# Funcion para mostrar los mensajes de la aplicacion
	global mensaje
	global mensajeVentana
	print texto	
	if mensaje != None and mensajeVentana != None:		# Verifica que ya se haya creado la ventana
		historial.insert(0, texto)						# Inserta el mensaje en el historial
		if len(historial) > CANT_MENSAJES:				# Si el historial llego a la cantidad definida, se elimina el mensaje mas antiguo		
			historial.pop()								# Elimina el mensaje mas antiguo
		mensaje.set('\n'.join(historial))				# Las siguientes 2 lineas establecen el historial de mensajes en la ventana
		mensajeVentana.grid(row=0, column=1, rowspan=CANT_MENSAJES, padx=50, pady=20)
	
	
def writeFile(linea):		# Funcion que va acumulando los datos que se reciben de la Arduino y guarda esos datos en el archivo correspondiente
	global lineas			# La palabra global quiere decir que esa variable esta definida por fuera de la funcion 
	global anteriorFecha
	hora = time.strftime("%H:%M:%S") 	# Obtiene la hora en formato Hora:Minutos:Segundos
	year = time.strftime("%Y")  		# Obtiene el anio
	mes = time.strftime("%m")			# Obtiene el mes
	dia = time.strftime("%d")			# Obtiene el dia
	fecha = dia + mes + year			# Une los datos para dejar la fecha en formato diaMesAnio	
	
	if fecha != anteriorFecha or len(lineas) > CANT_LINEAS: #Entra Si la fecha cambia (cambio de dia) o si ya se acumularon los datos requeridos para guardar en el archivo
		if not os.path.exists(RUTA + CARPETA_DATOS):					#Verifica si no existe la carpeta con nombre "DatosArduino"
			os.makedirs(RUTA + CARPETA_DATOS)
		
		if not os.path.exists(RUTA + CARPETA_DATOS + "/" + year):					#Verifica si no existe la carpeta con ese con nombre de ese anio 
			os.makedirs(RUTA + CARPETA_DATOS + "/" + year)							# Si no existe crea la carpeta
			
		if not os.path.exists(RUTA + CARPETA_DATOS + "/" + year + "/" + mes):					#Verifica si no existe la carpeta con nombre de ese mes 
			os.makedirs(RUTA + CARPETA_DATOS + "/" + year + "/" + mes)
						
		if os.path.exists(RUTA + CARPETA_DATOS + "/" + year + "/" + mes + "/" + "datos_"+fecha+".txt"):	# Verifica si el archivo con la fecha obtenida ya existe
			tipoEscritura = 'a'							# Si existe dejara la opcion que no creara un archivo nuevo, sino que escribira los datos en el archivo que ya existe
		else:
			tipoEscritura = 'w'							# Si no existe deja la opcion para crear el archivo nuevo
			imprimir("Se creo el archivo: " + RUTA + CARPETA_DATOS + "/" + year + "/" + mes + "/" + "datos_"+fecha+".txt")
			
		archivo = open(RUTA + CARPETA_DATOS + "/" + year + "/" + mes + "/" + "datos_"+fecha+".txt", tipoEscritura) # Abre el archivo de acuerdo a la opcion que se definio arriba
		
		for line in lineas: 			
			archivo.write(line + "\n") # Escribe dato a dato en el archivo lo que se ha acumulado			
		
		archivo.close()										# Se cierra el archivo 
		lineas = []			#Vacia la variable que va acumulando los lineas
		
		if fecha != anteriorFecha:
			anteriorFecha = fecha		# Si hay cambio de dia, actualiza la variable que permite verificar
	
	lineas.append(fecha +LIMIT + hora + LIMIT + linea)	# Agrega fecha y hora al comienzo de la linea y despues Agrega los datos a la variable que va acumulando
		
	

def comunicacion():			# Funcion que va leyendo los datos que llegan de la arduino
	global leido
	ready = select.select([arduino], [], [], 0.01)		# Select permite esperar datos que llegan de la Arduino sin bloquear el programa (Si no llega nada en 0.01 segundos sigue ejecutando)
	if ready[0]:										# Verifica si llego algun dato de la arduino
		leido += arduino.recv(1024)						# Como los datos a veces llegan cortados, se van acumulando todos los que llegan para despues organizarlos por lineas			
		limite = leido.find(SEPARADOR)					# Busca si en lo que va acumulado esta el separador que identifica donde empiezan y termina cada linea
		if limite != -1:								# Verifica si se encontro el Separador
			rec = leido[:limite]						# Obtiene una linea de lo que va acumulado desde ultimo separador encontrado hasta el siguiente									
			
			rec = filter(lambda x: x in LIMPIAR, rec) 	# Las Siguientes dos lineas eliminar cualquier letra que sea diferente a lo que se envio desde la arduino
			rec = rec.replace('\n', '').replace('\r','')
			
			if rec:										# Verificar que en rec si haya algo
				writeFile(rec)							# Envia la linea a la funcion writeFile
			leido = leido[limite+1:]					# Deja lista la variable leido para empezar a acumular desde el ultimo separador encontrado			
			
	
	ventana.after(1, comunicacion)  			# Permite ejecutar continuamente esta funcion (comunicacion-ejecuta la funcion cada 1 milesima de segundo)
	

 

def comando(boton, numero):		# Funcion que envia el comando a la arduino		
	imprimir("Se envio el comando: " + boton + ", #" + str(numero))	# Mostrar en consola
	arduino.send(numero)		# Envio del numero a la arduino
	

def salir(signal=None, frame=None):				# Funcion que se ejecuta cuando se cierra el programa
	global mensaje 
	global mensajeVentana
	mensaje = None
	mensajeVentana = None
	imprimir("Cerrando conexion Bluethooth...")
	if arduino != None: 	# Verifica que la conexion con arduino si se haya hecho, si la hizo la cierra
		arduino.close()
	
	if ventana != None: 	# Verifica que si la ventana esta creada, si esta creada la destruye		
		ventana.quit()		
	
	imprimir("Cerrando conexion Bluethooth: Finalizo correctamente")
	imprimir("Saliendo de la aplicacion...")
	sys.exit(0)
	
	
	


atexit.register(salir)							# Se registra la funcion salir. Cuando el programa se cierra, se ejecuta la funcion salir
signal.signal(signal.SIGINT, salir)

ventana = Tkinter.Tk()							# Se crea la ventana del programa
ventana.geometry(ANCHO + "x" + ALTO)   			# Establecer tamano de la ventana
ventana.title(NOMBRE)							# Establecer nombre de la ventana
arduino = bluetooth.BluetoothSocket( bluetooth.RFCOMM )	# Inicializar la conexion bluetooth



imprimir("Creando BOTONES...")
for boton in BOTONES.keys():		# Creacion de los botones
	botonTemporal = Tkinter.Button(ventana, text = boton, width=10, command = lambda a = boton, b = BOTONES[boton]: comando(a, b))	
	botonTemporal.grid(row=(int(BOTONES[boton])+1), column = 0)
	
imprimir("Creando BOTONES: Finalizo correctamente")

imprimir("Estableciendo conexion bluetooth...")
port = 1
address = "98:D3:32:30:D6:ED"			# Id del bluetooth del arduino
arduino.connect((address, port))		# Establecer los datos de conexion
arduino.setblocking(0)					# Establecer la conexion de tal manera que no bloquee el programa 

imprimir("Estableciendo conexion bluetooth: Finalizo correctamente")

imprimir("Creando Ventana...")


mensaje = Tkinter.StringVar()
mensajeVentana = Tkinter.Label(ventana, textvariable=mensaje, relief=Tkinter.RAISED, bg="white")
mensajeVentana.grid(row=1, column = 2)

ventana.after(1, comunicacion)
imprimir("Creando Ventana: Finalizo correctamente")
ventana.mainloop()			# ejecutar la ventana
