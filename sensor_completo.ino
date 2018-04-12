#include <Thread.h>
#include <SoftwareSerial.h>

int trig = 9;
int eco = 8;
int bomba = 13;
int valvula1 = 12;
int valvula2 = 11;
int valvula3 = 10;
int duracion;
int distancia;

unsigned long tiempoTrig= 0;       
unsigned long tiempoControl= 0;  
const long intervaloTrig = 1;    
const long intervaloControl = 300;       
const long intervaloEnviar = 250;  
const long intervaloRecibir = 250;  

ThreadController controlHilos = ThreadController();
Thread hiloRecibirComandos = Thread();
Thread hiloEnviarDatos = Thread();

SoftwareSerial bluetooth(10, 11); // RX, TX


void recibirComandos();
void enviarDatos();

void setup() {
	pinMode(trig,OUTPUT);
	pinMode(eco, INPUT);
	pinMode(bomba, OUTPUT);
	pinMode(valvula1, OUTPUT);
	pinMode(valvula2, OUTPUT);
	pinMode(valvula3, OUTPUT);
	
	Serial.begin(9600); 
	bluetooth.begin(9600);
	
	hiloRecibirComandos.onRun(recibirComandos);
	hiloRecibirComandos.setInterval(intervaloRecibir);
	
	hiloEnviarDatos.onRun(enviarDatos);
	hiloEnviarDatos.setInterval(intervaloEnviar);	
}

// Tarea 1: gestion de los sensores
void loop() {
	controlHilos.run();
	
	digitalWritetrig, HIGH;(); 
	unsigned long tiempoActual = millis();
	
	if(tiempoActual-tiempoTrig >= intervaloTrig){
		tiempoTrig = tiempoActual;
		digitalWritetrig, LOW();  	
		duracion = pulseIn(eco, HIGH);
		distancia = duracion / 58.2;
		Serial.println(distancia);	
		
		if(tiempoActual-tiempoControl >= intervaloControl){
			tiempoControl = tiempoActual;
			if(distancia <=50  && distancia >=10){
				digitalWrite(valvula1, HIGH());	
			}else{
				digitalWrite(valvula1, LOW());
			}
			if(distancia <=40 && distancia >=10){
				digitalWrite(valvula2, HIGH());	
			}
			else{
				digitalWrite(valvula2, LOW());	
			}
			if(distancia <=30 && distancia >=10){
				digitalWrite(valvula3, HIGH());	
			}
			else{
				digitalWrite(valvula3, LOW());	
			}
			if(distancia >= 50){
				digitalWrite(bomba, HIGH());		
			}
			if(distancia <= 10){
				digitalWrite(bomba, LOW());
			}
		}
		tiempoTrig
	}
 
	
}


// Tarea 2: Recibir comandos de la raspberry
void recibirComandos(){
	if (bluetooth.available()){
		int comando = bluetooth.read();
		switch(comando){						
			case 5:
				digitalWrite(bomba, HIGH());
				break;
			case 6:
				digitalWrite(bomba, LOW());
				break;
			case 7:
				digitalWrite(valvula1, HIGH());
				break;
			case 8:
				digitalWrite(valvula1, LOW());
				break;
			case 9:
				digitalWrite(valvula2, HIGH());
				break;
			case 10:
				digitalWrite(valvula2, LOW());
				break;
			case 12:
				digitalWrite(valvula3, HIGH());
				break;
			case 13:
				digitalWrite(valvula3, LOW());
				break;
			default:
				break;
		}

	}
}

// Tarea 3: Enviar datos a la raspberry
void enviarDatos(){
	
	bool trigOn = digitalRead(trig) == HIGH;
	bool ecoOn = digitalRead(ecoOn) == HIGH;
	bool bombaOn = digitalRead(bombaOn) == HIGH;
	bool valvula1On = digitalRead(valvula1On) == HIGH;
	bool valvula2On = digitalRead(valvula2On) == HIGH;
	bool valvula3On = digitalRead(valvula3On) == HIGH;
	
	bluetooth.write(distancia + "," + duracion + "," + trigOn + "," + ecoOn + "," + 
		"," + bombaOn + "," + valvula1On + "," + valvula2On + "," + valvula3On);

}

