import machine
import utime as time
import MQ2_data
import ubinascii
import ujson
import network

# import paho.mqtt.publish as publish
from umqtt.simple import MQTTClient

global client_id


def connect_and_subscribe(mqtt_server, user, password):
    client_id = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, mqtt_server, user=user, password=password)
    client.connect()
    print(
        "Connected to %s MQTT broker, subscribed to %s topic"
        % (settings["mqtt_server"], settings["mqtt_topic"])
    )
    return client


def mqttrestart():
    print("Conexion con broker fallo.")
    machine.reset()


def subscribe_message(topic, msg):
    print((topic, msg))


def get_data(MQ2, Ro):
    CH4 = MQ2_data.MQGetGasPercentage(MQ2_data.MQRead(MQ2) / Ro, MQ2_data.GAS_CH4)
    Propane = MQ2_data.MQGetGasPercentage(
        MQ2_data.MQRead(MQ2) / Ro, MQ2_data.GAS_PROPANE
    )
    Smoke = MQ2_data.MQGetGasPercentage(MQ2_data.MQRead(MQ2) / Ro, MQ2_data.GAS_SMOKE)
    CO = MQ2_data.MQGetGasPercentage(MQ2_data.MQRead(MQ2) / Ro, MQ2_data.GAS_CO)
    LPG = MQ2_data.MQGetGasPercentage(MQ2_data.MQRead(MQ2) / Ro, MQ2_data.GAS_LPG)
    message = ujson.dumps(
        {"CH4": CH4, "Propane": Propane, "Smoke": Smoke, "CO": CO, "LPG": LPG}
    )
    return message


if __name__ == "__main__":
    try:
        with open("settings.json", "r") as file:
            settings = file.read()
        settings = ujson.loads(settings)

        print("Iniciando...")
        print("Calibrando...")
        MQ2 = machine.ADC(machine.Pin(34))  # define the analog input by sensor
        MQ2.atten(machine.ADC.ATTN_11DB)
        Ro = MQ2_data.MQCalibration(MQ2)
        print("La calibracion esta terminada...")
        print("Ro={} kohm".format(Ro))

        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(settings["ssid"], settings["password_wlan"])  # Connect to an AP

        while not station.isconnected():
            time.sleep(0.1)
        print("Conectado a la red wlan")

        try:
            print("Conectandose a mqttserver")
            client = connect_and_subscribe(
                settings["mqtt_server"],
                settings["mqtt_user"],
                settings["mqtt_password"],
            )
        except Exception as e:
            pass
        while station.isconnected() == False:
            pass
        print("Connection successful")
        print(station.ifconfig())

        while True:
            message = get_data(MQ2, Ro)
            print(
                "CH4: {0:,.2f}ppm  Propano: {0:,.2f}ppm  Smoke: {0:,.2f}ppm CO: {0:,.2f}ppm  LPG: {0:,.2f}ppm".format(
                    message["CH4"], message["Propane"], message["Smoke"], message["CO"],message["LPG"]
                )
            )
            try:
                client.publish(settings["mqtt_topic"], message.encode("utf-8"))
            except:
                try:
                    print("Conectandose a mqttserver")
                    client = connect_and_subscribe()
                except Exception as e:
                    # mqttrestart()
                    pass
            time.sleep(5)
    except KeyboardInterrupt as e:
        # client.disconnect()
        print(e)
        machine.reset()
        print("Apagando...")
