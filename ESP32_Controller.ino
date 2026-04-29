#include <WiFi.h>
#include <WebSocketsServer.h>

const char *ssid = "WunmisiPhone";
const char *password = "Nothing1";

const int NUM_SLOTS = 10;
const int RELAY_PINS[NUM_SLOTS] = {4, 5, 6, 7, 15, 16, 17, 18, 8, 9};

// true = slot wired on NO (LOW turns magnet ON)
// false = slot wired on NC (HIGH turns magnet ON)
const bool wiredOnNO[NUM_SLOTS] = {true, true, false, false, false, false, false, false, false, false};

WebSocketsServer webSocket(81);
bool clientConnected = false;
uint8_t clientId = 0;
bool slotHolding[NUM_SLOTS];

void wifi_connect()
{
    WiFi.begin(ssid, password);
    Serial.print("WiFi");
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.print(" ");
    Serial.println(WiFi.localIP());
}

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

void sendStatus()
{
    if (!clientConnected)
        return;
    String msg = "STATUS ";
    for (int i = 0; i < NUM_SLOTS; i++)
    {
        msg += slotHolding[i] ? "1" : "0";
    }
    webSocket.sendTXT(clientId, msg);
}

void ws_on_connect(uint8_t num)
{
    clientId = num;
    clientConnected = true;
    Serial.println("Client connected");
    sendStatus();
}

void ws_on_disconnect()
{
    clientConnected = false;
    Serial.println("Client disconnected");
}

void ws_on_text(uint8_t *payload, size_t length)
{
    String cmd = String((char *)payload).substring(0, length);
    cmd.trim();

    if (cmd.startsWith("release "))
    {
        int slot = cmd.substring(8).toInt();
        releaseSlot(slot);
        sendStatus();
    }
    else if (cmd.startsWith("hold "))
    {
        int slot = cmd.substring(5).toInt();
        holdSlot(slot);
        sendStatus();
    }
    else if (cmd == "release_all")
    {
        releaseAll();
        sendStatus();
    }
    else if (cmd == "hold_all")
    {
        holdAll();
        sendStatus();
    }
    else if (cmd == "status")
    {
        sendStatus();
    }
}

void ws_on_event(uint8_t num, WStype_t type, uint8_t *payload, size_t length)
{
    switch (type)
    {
    case WStype_CONNECTED:
        ws_on_connect(num);
        break;
    case WStype_DISCONNECTED:
        ws_on_disconnect();
        break;
    case WStype_TEXT:
        ws_on_text(payload, length);
        break;
    default:
        break;
    }
}

void ws_setup()
{
    webSocket.begin();
    webSocket.onEvent(ws_on_event);
    Serial.println("WebSocket on :81");
}

void relay_setup()
{
    for (int i = 0; i < NUM_SLOTS; i++)
    {
        pinMode(RELAY_PINS[i], OUTPUT);
        digitalWrite(RELAY_PINS[i], wiredOnNO[i] ? LOW : HIGH);
        slotHolding[i] = true;
    }
}

void setup()
{
    Serial.begin(115200);
    wifi_connect();
    relay_setup();
    ws_setup();
}

void loop()
{
    webSocket.loop();

    if (Serial.available())
    {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        if (cmd.startsWith("release "))
        {
            releaseSlot(cmd.substring(8).toInt());
        }
        else if (cmd.startsWith("hold "))
        {
            holdSlot(cmd.substring(5).toInt());
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
            for (int i = 0; i < NUM_SLOTS; i++)
            {
                Serial.printf("Slot %d: %s\n", i, slotHolding[i] ? "HOLDING" : "RELEASED");
            }
        }
    }
}