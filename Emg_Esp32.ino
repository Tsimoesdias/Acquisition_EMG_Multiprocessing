#include <Arduino.h>
#include "WiFi.h"
#include <ArduinoJson.h>
#include <math.h>


//Atualização do código do Daniel C.
//Criação do Multiprocessing (loop1 e loop2)

// Replace with your network credentials
const char* ssid     = "ESP32-Access-Point";
const char* password = "123456789";

// Set web server port number to 80
WiFiServer server(80);

#define BUFF_SIZE 64
#define Ts 1000

char a = 'a';
char s = 's';
char d = 'd';
char c = 'c';
volatile int temBufferPronto;
volatile int flagAcq = 0;
int bufferIndex = 0;
const uint16_t port = 15200;
int contador_de_timeout = 0;
const int analogIn = 4;
int  MValue=0;
int TempC;
float Voltage;
float x = 0;
int bip = 1;
WiFiClient client;
String command;
String command_th;
String command_val;
unsigned long t0, t1, t2;
//int LED_BUILTIN = 2;
int led_sts = 1;
float buf1[BUFF_SIZE];
float buf2[BUFF_SIZE];
//float buf[BUFF_SIZE];
hw_timer_t * timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;
const size_t CAPACITY = JSON_ARRAY_SIZE(BUFF_SIZE);
int cont = 1;
String pacote;
int flag = 0;
int buf1_pronto = 0;
int buf2_pronto = 0;

String prepararDado1(){

    // allocate the memory for the document
    StaticJsonDocument<CAPACITY> doc;

    // create an empty array
    JsonArray msg = doc.to<JsonArray>();
    for (int i=0; i< BUFF_SIZE; i++)
        msg.add(buf1[i]);

    // serialize the array and sed the result to Serial
    String json;
    serializeJson(msg, json);
    //Serial.println("Data ready to send...");
    return json;
}

String prepararDado2(){

    // allocate the memory for the document
    StaticJsonDocument<CAPACITY> doc;

    // create an empty array
    JsonArray msg = doc.to<JsonArray>();
    for (int i=0; i< BUFF_SIZE; i++)
        msg.add(buf2[i]);

    // serialize the array and sed the result to Serial
    String json;
    serializeJson(msg, json);
    //Serial.println("Data ready to send...");
    return json;
}

void flipLED(){
    if (led_sts == 1){
      led_sts = 0;
    }
    else{
      led_sts = 1;
    }
    digitalWrite(LED_BUILTIN, led_sts);
}

void ledFlag(){
    command_th = command[0];
    command_val = command.substring(1);
    //Serial.print(command_th);
    //Serial.print("?");
    //Serial.print(command_val);
    //Serial.print("!");
    Serial.print(command_val);
    if (command_th.equals("a")){
      digitalWrite(LED_BUILTIN, 1);
      //Serial.print(command_th);
      Serial2.print(a);
    } 
    else{
      digitalWrite(LED_BUILTIN, 0);
    }

    if (command_val.equals("s")){
      Serial2.print(s);
    }

    if (command_val.equals("d")){
      Serial2.print(d);
    }

}

void montarBuffer1(){
  
  buf1[bufferIndex] = Voltage;
  bufferIndex++;

  if (bufferIndex > BUFF_SIZE-1){
    buf1_pronto = 1;
   // temBufferPronto++;
    //Serial.println(temBufferPronto);
    bufferIndex = 0;
    //Serial.println("Buffer Ready");
  }
}

void montarBuffer2(){
  
  buf2[bufferIndex] = Voltage;
  bufferIndex++;

  if (bufferIndex > BUFF_SIZE-1){
    buf2_pronto = 1;
   // temBufferPronto++;
    //Serial.println(temBufferPronto);
    bufferIndex = 0;
    //Serial.println("Buffer Ready");
  }
}



void leituraEMG(){

  MValue = analogRead(35); //34
  Voltage = ((((3.3 / 4096.0) *(MValue))-1.6));

}

 
//void IRAM_ATTR onTimer() {
//  
//  portENTER_CRITICAL_ISR(&timerMux);
//   flagAcq = 1;
//  portEXIT_CRITICAL_ISR(&timerMux);
//  
//}



void setup() {

  //Serial.begin(115200);
  Serial.begin(9600);
  Serial2.begin(9600);

  // Connect to Wi-Fi network with SSID and password
  Serial.print("Setting AP (Access Point)…");
  // Remove the password parameter, if you want the AP (Access Point) to be open
  WiFi.softAP(ssid, password);

  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(IP);
  
  server.begin();
  buf1_pronto = 0;
  buf2_pronto = 0;

  
  pinMode (LED_BUILTIN, OUTPUT);
//  timer = timerBegin(0, 80, true);
//  timerAttachInterrupt(timer, &onTimer, true);
//  timerAlarmWrite(timer, Ts, true);
//  timerAlarmEnable(timer);
  Serial.println("Timer configurado!");
  xTaskCreatePinnedToCore(loop2, "loop2", 8192, NULL, 1, NULL, 0);//Cria a tarefa "loop2()" com prioridade 1, atribuída ao core 0
  delay(1);
}

void loop() {
WiFiClient client = server.available();   // Listen for incoming clients

  if (client) {                             // If a new client connects,
    Serial.println("New Client.");          // print a message out in the serial port
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if(flag == 1){
        buf1_pronto = 1;
        if (buf1_pronto == 1){
          client.print(prepararDado1()); //Envia o pacote de dados via sockets
          buf1_pronto = 0;
          }
        else if(buf2_pronto == 1){
          client.print(prepararDado2()); //Envia o pacote de dados via sockets
          buf2_pronto = 0;
          }
        
        flag = 0;      
        }    
       command = client.readStringUntil('\n');
       command.trim();        //kill whitespace
       ledFlag(); 
     }

  client.stop();
  Serial.println("Client disconnected");
 }
}

void loop2(void*z)//Atribuímos o loop2 ao core 0, com prioridade 1
{
  //Serial.print("comecou loop2");
  while(1){
    for(int i = 0; i<BUFF_SIZE; i++){
        leituraEMG();
        if(cont == 1){
          montarBuffer1();
          }
        else if(cont == 2){
          montarBuffer2();
          }
        delay(1);  
    }
    
    if(cont == 1){
      cont = 2;
      } 
    else if(cont == 2) {
      cont = 1;
    }
    
    flag = 1;  
    
}
}
