#include <WiFiS3.h>

#include <DHT.h>
#include <ArduinoJson.h>// The official JSON library

#define DHTPIN 10     // The digital pin the DHT sensor is connected to
#define DHTTYPE DHT11 // The type of sensor you're using (DHT11, DHT22, etc.)

// Initialize the sensor
DHT dht(DHTPIN, DHTTYPE);
const char* serverName = "192.168.0.22";
#define server_port 80

const char *ssid_Router = ""; // Add your wifi name 2G works
const char *password_Router = ""; // add your router password
WiFiServer  server(server_port);

// Variable to store the HTTP request
String header;
// Auxiliar variables to store the current output state
String PIN_LEDState = "OFF";

// Current time
unsigned long currentTime = millis();
// Previous time
unsigned long previousTime = 0;
// Define timeout time in milliseconds (example: 2000ms = 2s)
const long timeoutTime = 2000;

void setup() {
  Serial.begin(115200);
  // Initialize the output variables as outputs
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  // Connect to Wi-Fi network with SSID and password
  Serial.print("Connecting to ");
  Serial.println(ssid_Router);
  WiFi.begin(ssid_Router, password_Router);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // Print local IP address and start web server
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
  dht.begin();
}
void sendPostRequest(float *temp, float *hum) {
  // Create a JSON object
  JsonDocument jsonPayload;
  jsonPayload["temp"] = *temp;
  jsonPayload["humidity"] = *hum;
  jsonPayload["sensor_id"] = "arduino-uno";

  // Convert the JSON object to a string
  String jsonString;
  serializeJson(jsonPayload, jsonString);

  Serial.print("Connecting to server: ");
  Serial.println(serverName);

  WiFiClient client;
  // Use WiFiClient to create a POST request
  if (client.connect(serverName, 8000)) {
    Serial.println("Connected to server");
    client.println("POST /temp-humidity HTTP/1.1");
    client.print("Host: ");
    client.println(serverName);
    client.println("Content-Type: application/json");
    client.print("Content-Length: ");
    client.println(jsonString.length());
    client.println();
    client.print(jsonString);

    Serial.print("Sending JSON: ");
    Serial.println(jsonString);
    
    // Optional: Read the response
    while(client.connected()) {
      if(client.available()){
        String line = client.readStringUntil('\n');
        Serial.println(line);
      }
    }
    client.stop();
    Serial.println("Disconnected from server.");
  } else {
    Serial.println("Connection to server failed!");
  }
}
void temperature_reading(float *t, float *h){


 delay(2000);
  // Reading temperature or humidity takes about 250 milliseconds!
  *h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  *t = dht.readTemperature();

  // Check if any reads failed and exit early (to try again).
  if (isnan(*h) || isnan(*t)) {
    Serial.println(F("Failed to read from DHT sensor!"));
  }
  else {

    sendPostRequest(t, h);
  }

  Serial.print(F("Humidity: "));
  Serial.print(*h);
  Serial.print(F("%  Temperature: "));
  Serial.print(*t);
  Serial.println(F("°C"));

}

void loop() {
  float h,t;
  WiFiClient client = server.available();  // Listen for incoming clients
  temperature_reading(&t,&h);
  if (client) {                            // If a new client connects,
    Serial.println("New Client.");         // print a message out in the serial port
    String currentLine = "";               // make a String to hold incoming data from the client
    currentTime = millis();
    previousTime = currentTime;
    while (client.connected() && currentTime - previousTime <= timeoutTime) {  // loop while the client's connected
      currentTime = millis();
      if (client.available()) {  // if there's bytes to read from the client,
        char c = client.read();  // read a byte, then
        Serial.write(c);         // print it out the serial monitor
        header += c;
        if (c == '\n') {  // if the byte is a newline character
          // if the current line is blank, you got two newline characters in a row.
          // that's the end of the client HTTP request, so send a response:
          Serial.write("Reading!!!!");
          if (currentLine.length() == 0) {
              
            // HTTP headers always start with a response code (e.g. HTTP/1.1 200 OK)
            // and a content-type so the client knows what's coming, then a blank line:
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println("Connection: close");
            client.println();
            // turns the GPIOs on and off
            if (header.indexOf("GET /LED_BUILTIN/ON") >= 0) {
              Serial.println("LED_BUILTIN ON");
              PIN_LEDState = "ON";
              digitalWrite(LED_BUILTIN, HIGH);
            } else if (header.indexOf("GET /LED_BUILTIN/OFF") >= 0) {
              Serial.println("LED_BUILTIN OFF");
              PIN_LEDState = "OFF";
              digitalWrite(LED_BUILTIN, LOW);
            }
            // Display the HTML web page
            client.println("<!DOCTYPE html><html>");
            client.println("<head> <title>Control Board Web Server</title> <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
            client.println("<link rel=\"icon\" href=\"data:,\">");
            // CSS to style the on/off buttons
            // Feel free to change the background-color and font-size attributes to fit your preferences
            client.println("<style>html {font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}");
            client.println(" h1{color: #0F3376; padding: 2vh;} p{font-size: 1.5rem;}");
   
            client.println("</p>");
            client.println(".button{background-color: #4286f4; display: inline-block; border: none; border-radius: 4px; color: white; padding: 16px 40px;text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}");
            client.println(".button2{background-color: #4286f4;display: inline-block; border: none; border-radius: 4px; color: white; padding: 16px 40px;text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}</style></head>");
            // Web Page Heading
            client.println("<body><h1>Control Board Web Server</h1>");
            client.println("<p>GPIO state: " + PIN_LEDState + "</p>");
            client.println("<p><a href=\"/LED_BUILTIN/ON\"><button class=\"button button2\">ON</button></a></p>");
            client.println("<p><a href=\"/LED_BUILTIN/OFF\"><button class=\"button button2\">OFF</button></a></p>");
            client.print("<p>Current Temperature: ");
            client.print(t, 2); // Prints the float 't' with 2 decimal places
            client.print(" Current Humidity: ");
            client.print(h, 2); // Prints the float 'h' with 2 decimal places
            client.print("</p>"); // Prints the float 'h' with 2 decimal places
            client.println("</body></html>");
            // The HTTP response ends with another blank line
            client.println();
            // Break out of the while loop
            break;
          } else {  // if you got a newline, then clear currentLine
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      }
    }
    // Clear the header variable
    header = "";
    // Close the connection
    client.stop();
    Serial.println("Client disconnected.");
    Serial.println("");
  }
  

}