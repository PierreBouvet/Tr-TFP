#include <Arduino.h>

// Define Pins
const int TRIGGER_INPUT_PIN = 16;  // RX2 - Input from TFP/Master
const int TRIGGER_OUTPUT_PIN = 17; // TX2 - Output to Laser
const int DEBUG_LED = 2; // Integrated LED

// Protocol Constants
const char* CMD_CONFIG = "CONFIG";
const char* CMD_DATA = "DATA";
const char* CMD_START = "START";
const char* CMD_STOP = "STOP";
const char* CMD_RESET = "RESET";

// Data Storage
// Max delays we can store. 
// Assuming 4 bytes per delay (uint32_t for microseconds), 1000 delays = 4KB. ESP32 has plenty of RAM.
const int MAX_DELAYS = 10000; 
volatile uint32_t delay_list[MAX_DELAYS];
volatile int delay_count = 0;
volatile int current_index = 0;

volatile bool is_running = false;
volatile bool trigger_received = false;

// Interrupt Service Routine for Input Trigger
void IRAM_ATTR on_trigger_input() {
    if (is_running && delay_count > 0) {
        // We set a flag or process directly? 
        // For distinct delays, blocking inside ISR for MS is bad if delays are long.
        // However, if we need strict timing relative to input, we might need to use hardware timer.
        // For simplicity and "ms" scale delays, we can use a hardware timer or busy wait if dedicated.
        // Let's use a flag and handle in loop if precision < 10us is acceptable. 
        // IF precision needs to be high, we should use a hardware timer.
        
        // BETTER APPROACH: Use a hardware timer to fire the output pulse after 'current_delay'
        // For now, let's try a simple approach: 
        // 1. Read delay for this step
        // 2. Wait
        // 3. Pulse
        // 4. Increment index
        
        // NOTE: doing delayMicroseconds inside ISR is blocking. 
        // If delays are > 10ms, this crashes the watchdog.
        // So we MUST NOT do long wait in ISR.
        
        trigger_received = true;
    }
}

void setup() {
    Serial.begin(115200);
    
    pinMode(TRIGGER_INPUT_PIN, INPUT_PULLDOWN); // Use Pulldown if active high
    pinMode(TRIGGER_OUTPUT_PIN, OUTPUT);
    pinMode(DEBUG_LED, OUTPUT);
    
    digitalWrite(TRIGGER_OUTPUT_PIN, LOW);
    digitalWrite(DEBUG_LED, LOW);
    
    // Attach Interrupt
    attachInterrupt(digitalPinToInterrupt(TRIGGER_INPUT_PIN), on_trigger_input, RISING);
    
    Serial.println("ESP32 Trigger System Ready");
    Serial.println("Send: CONFIG <num_delays>");
}

void loop() {
    // Handle Serial Commands
    if (Serial.available() > 0) {
        String line = Serial.readStringUntil('\n');
        line.trim();
        
        if (line.startsWith(CMD_CONFIG)) {
            // CONFIG 100
            int spaceIdx = line.indexOf(' ');
            if (spaceIdx > 0) {
                int requested_count = line.substring(spaceIdx + 1).toInt();
                if (requested_count <= MAX_DELAYS) {
                    delay_count = requested_count;
                    current_index = 0;
                    is_running = false;
                    Serial.print("OK CONFIG "); Serial.println(delay_count);
                } else {
                    Serial.println("ERR MAX_DELAYS exceeded");
                }
            }
        } 
        else if (line.startsWith(CMD_DATA)) {
            // DATA index value_us
            // Example: DATA 0 1000
            // Block read might be faster for bulk, but this is safer for text protocol
            int firstSpace = line.indexOf(' ');
            int secondSpace = line.indexOf(' ', firstSpace + 1);
            
            if (firstSpace > 0 && secondSpace > 0) {
                int index = line.substring(firstSpace + 1, secondSpace).toInt();
                long value = line.substring(secondSpace + 1).toInt();
                
                if (index >= 0 && index < delay_count) {
                    delay_list[index] = value;
                    // Echo back occasionally or just OK
                    // Serial.println("OK DATA");
                }
            }
        }
        else if (line.startsWith(CMD_START)) {
            current_index = 0;
            is_running = true;
            trigger_received = false;
            Serial.println("OK START");
        }
        else if (line.startsWith(CMD_STOP)) {
            is_running = false;
            Serial.println("OK STOP");
        }
        else if (line.startsWith(CMD_RESET)) {
            is_running = false;
            delay_count = 0;
            current_index = 0;
            Serial.println("OK RESET");
        }
    }
    
    // Handle Trigger Action (outside ISR to avoid watchdog crashes on long delays)
    if (trigger_received) {
        trigger_received = false; // logic handled
        
        if (is_running && delay_count > 0) {
            unsigned long delay_us = delay_list[current_index];
            
            // Wait the specified delay
            // For delays > 10000us (10ms), use delay() to yield
            if (delay_us > 15000) {
                delay(delay_us / 1000);
                delayMicroseconds(delay_us % 1000);
            } else {
                delayMicroseconds(delay_us);
            }
            
            // Generate Pulse (10us width)
            digitalWrite(TRIGGER_OUTPUT_PIN, HIGH);
            digitalWrite(DEBUG_LED, HIGH);
            delayMicroseconds(10); 
            digitalWrite(TRIGGER_OUTPUT_PIN, LOW);
            digitalWrite(DEBUG_LED, LOW);
            
            // Advance Index
            current_index++;
            if (current_index >= delay_count) {
                current_index = 0; // Loop
            }
        }
    }
}
