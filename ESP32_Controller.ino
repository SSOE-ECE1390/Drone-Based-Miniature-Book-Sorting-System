#include <Arduino.h>

const int NUM_SLOTS = 10;
const int RELAY_PINS[NUM_SLOTS] = {4, 5, 6, 7, 15, 16, 17, 18, 8, 9};

// true = slot wired on NO (LOW turns magnet ON)
// false = slot wired on NC (HIGH turns magnet ON)
const bool wiredOnNO[NUM_SLOTS] = {true, true, false, false, false, false, false, false, false, false};

bool slotHolding[NUM_SLOTS];

void releaseSlot(int slot)
{
    if (slot < 0 || slot >= NUM_SLOTS)
        return;
    digitalWrite(RELAY_PINS[slot], wiredOnNO[slot] ? HIGH : LOW);
    slotHolding[slot] = false;
    Serial.printf("Slot %d: RELEASED\n", slot);
}

void holdSlot(int slot)
{
    if (slot < 0 || slot >= NUM_SLOTS)
        return;
    digitalWrite(RELAY_PINS[slot], wiredOnNO[slot] ? LOW : HIGH);
    Serial.println(digitalRead(RELAY_PINS[slot]));
    slotHolding[slot] = true;
    Serial.printf("Slot %d: HOLDING\n", slot);
}

void releaseAll()
{
    for (int i = 0; i < NUM_SLOTS; i++)
        releaseSlot(i);
}

void holdAll()
{
    for (int i = 0; i < NUM_SLOTS; i++)
        holdSlot(i);
}

void printStatus()
{
    for (int i = 0; i < NUM_SLOTS; i++)
    {
        Serial.printf("Slot %d: %s\n", i, slotHolding[i] ? "HOLDING" : "RELEASED");
    }
}

void processSerialCommand()
{
    if (Serial.available())
    {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        if (cmd.startsWith("release "))
        {
            int slot = cmd.substring(8).toInt();
            releaseSlot(slot);
        }
        else if (cmd.startsWith("hold "))
        {
            int slot = cmd.substring(5).toInt();
            holdSlot(slot);
        }
        else if (cmd == "release_all")
        {
            releaseAll();
        }
        else if (cmd == "hold_all")
        {
            holdAll();
        }
        else if (cmd == "status")
        {
            printStatus();
        }
    }
}

void relay_setup()
{
    for (int i = 0; i < NUM_SLOTS; i++)
    {
        pinMode(RELAY_PINS[i], OUTPUT);
        if (i <= 5)
        {
            // slots 0-5: start held
            digitalWrite(RELAY_PINS[i], wiredOnNO[i] ? LOW : HIGH);
            slotHolding[i] = true;
        }
        else
        {
            // slots 6-8: start released
            digitalWrite(RELAY_PINS[i], wiredOnNO[i] ? HIGH : LOW);
            slotHolding[i] = false;
        }
    }
}

void setup()
{
    Serial.begin(115200);
    relay_setup();
    Serial.println("ESP32 Shelf Controller started - Serial mode");
}

void loop()
{
    processSerialCommand();
}