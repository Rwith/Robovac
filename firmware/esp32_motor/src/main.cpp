// ESP32 motor controller — skeleton (Milestone M2).
//
// Responsibilities:
//   * parse "V <l> <r>" / "S" commands from the SBC
//   * drive the TB6612FNG to hit target wheel speeds (add a PID later)
//   * count quadrature encoders on interrupts
//   * read BNO055 yaw
//   * stream "O <encL> <encR> <yaw>" odometry back at ~50 Hz
//
// See README.md for the serial protocol and wiring.

#include <Arduino.h>

// --- Pins (adjust to your wiring) ---
constexpr int PIN_ENC_L_A = 34;
constexpr int PIN_ENC_R_A = 35;
constexpr int PIN_MOTOR_L_PWM = 25;
constexpr int PIN_MOTOR_R_PWM = 26;

volatile long encL = 0;
volatile long encR = 0;
float targetLeft = 0.0f;   // m/s
float targetRight = 0.0f;  // m/s

void IRAM_ATTR onEncL() { encL++; }
void IRAM_ATTR onEncR() { encR++; }

void handleCommand(const String &line) {
  if (line.length() == 0) return;
  if (line[0] == 'S') {
    targetLeft = targetRight = 0.0f;
    return;
  }
  if (line[0] == 'V') {
    int sp = line.indexOf(' ');
    int sp2 = line.indexOf(' ', sp + 1);
    targetLeft = line.substring(sp + 1, sp2).toFloat();
    targetRight = line.substring(sp2 + 1).toFloat();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_ENC_L_A, INPUT_PULLUP);
  pinMode(PIN_ENC_R_A, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_L_A), onEncL, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_R_A), onEncR, RISING);
  // TODO: configure LEDC PWM channels for PIN_MOTOR_*_PWM.
  // TODO: init BNO055 over I2C.
}

void loop() {
  while (Serial.available()) {
    handleCommand(Serial.readStringUntil('\n'));
  }

  // TODO: PID from (targetLeft/Right vs. measured wheel speed) -> motor PWM.

  static unsigned long last = 0;
  if (millis() - last >= 20) {  // ~50 Hz
    last = millis();
    float yaw = 0.0f;  // TODO: read from BNO055
    Serial.printf("O %ld %ld %.4f\n", encL, encR, yaw);
  }
}
