// Simplified FH5 Display without ArduinoJson
#include <WiFi.h>
#include <WiFiUdp.h>
#include <TFT_eSPI.h>

// WiFi credentials
const char* ssid = "SSID HERE";
const char* password = "Password here";

// UDP settings
WiFiUDP udp;
const int udpPort = 8080;

// Display
TFT_eSPI tft = TFT_eSPI();

// Telemetry data structure
struct TelemetryData {
  float speed_kmh = 0;
  float rpm = 0;
  int throttle = 0;
  int brake = 0;
  int gear = 0;
  float accel_z = 0;
} telemetry;

// Display settings
#define SPEED_COLOR TFT_CYAN
#define RPM_COLOR TFT_GREEN
#define THROTTLE_COLOR TFT_YELLOW
#define BRAKE_COLOR TFT_RED
#define BG_COLOR TFT_BLACK
#define TEXT_COLOR TFT_WHITE

void setup() {
  Serial.begin(115200);
  
  // Initialize display
  tft.init();
  tft.setRotation(1); // Landscape mode
  tft.fillScreen(BG_COLOR);
  tft.setTextColor(TEXT_COLOR);
  
  // Show startup screen
  tft.setTextSize(2);
  tft.setCursor(50, 100);
  tft.println("FH5 Telemetry");
  tft.setCursor(80, 130);
  tft.println("Connecting...");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  // Start UDP
  udp.begin(udpPort);
  
  // Clear screen and draw UI
  setupDisplay();
}

void setupDisplay() {
  tft.fillScreen(BG_COLOR);
  
  // Title
  tft.setTextSize(2);
  tft.setTextColor(TFT_WHITE);
  tft.setCursor(100, 10);
  tft.println("FORZA HORIZON 5");
  
  // Static labels
  tft.setTextSize(1);
  tft.setTextColor(TFT_LIGHTGREY);
  tft.setCursor(10, 50);
  tft.println("SPEED");
  tft.setCursor(10, 100);
  tft.println("RPM");
  tft.setCursor(10, 150);
  tft.println("GEAR");
  tft.setCursor(200, 50);
  tft.println("THROTTLE");
  tft.setCursor(200, 100);
  tft.println("BRAKE");
  tft.setCursor(200, 150);
  tft.println("ACCEL");
}

void updateDisplay() {
  // Speed (large display)
  tft.setTextSize(4);
  tft.setTextColor(SPEED_COLOR, BG_COLOR);
  tft.setCursor(10, 70);
  tft.printf("%3.0f", telemetry.speed_kmh);
  
  tft.setTextSize(2);
  tft.setCursor(120, 85);
  tft.println("km/h");
  
  // RPM
  tft.setTextSize(2);
  tft.setTextColor(RPM_COLOR, BG_COLOR);
  tft.setCursor(60, 100);
  tft.printf("%4.0f", telemetry.rpm);
  
  // Gear
  tft.setTextSize(3);
  tft.setTextColor(TFT_ORANGE, BG_COLOR);
  tft.setCursor(50, 150);
  if (telemetry.gear == 0) {
    tft.println("R");
  } else if (telemetry.gear == 1) {
    tft.println("N");
  } else {
    tft.printf("%d", telemetry.gear - 1);
  }
  
  // Throttle
  tft.setTextSize(2);
  tft.setTextColor(THROTTLE_COLOR, BG_COLOR);
  tft.setCursor(260, 50);
  tft.printf("%3d%%", telemetry.throttle);
  
  // Brake
  tft.setTextColor(BRAKE_COLOR, BG_COLOR);
  tft.setCursor(260, 100);
  tft.printf("%3d%%", telemetry.brake);
  
  // Acceleration
  tft.setTextSize(1);
  tft.setTextColor(TFT_MAGENTA, BG_COLOR);
  tft.setCursor(260, 150);
  tft.printf("%+.2f", telemetry.accel_z);
}

// Simple string parsing instead of JSON
void parseSimpleData(String data) {
  // Expected format: "speed,rpm,throttle,brake,gear,accel"
  int commaIndex = 0;
  int lastIndex = 0;
  int valueIndex = 0;
  
  for (int i = 0; i <= data.length(); i++) {
    if (data.charAt(i) == ',' || i == data.length()) {
      String value = data.substring(lastIndex, i);
      
      switch (valueIndex) {
        case 0: telemetry.speed_kmh = value.toFloat(); break;
        case 1: telemetry.rpm = value.toFloat(); break;
        case 2: telemetry.throttle = value.toInt(); break;
        case 3: telemetry.brake = value.toInt(); break;
        case 4: telemetry.gear = value.toInt(); break;
        case 5: telemetry.accel_z = value.toFloat(); break;
      }
      
      lastIndex = i + 1;
      valueIndex++;
    }
  }
}

void loop() {
  // Check for UDP packets
  int packetSize = udp.parsePacket();
  if (packetSize) {
    String receivedData = "";
    while (udp.available()) {
      receivedData += (char)udp.read();
    }
    
    parseSimpleData(receivedData);
    updateDisplay();
    
    Serial.printf("Speed: %.1f km/h | RPM: %.0f | Gear: %d\n", 
                  telemetry.speed_kmh, telemetry.rpm, telemetry.gear);
  }
  
  delay(50); // Update at ~20 Hz
}
