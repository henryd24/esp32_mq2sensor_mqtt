import machine
import utime as time
import MQ2_data
import ubinascii
import ujson
import network

from umqtt.simple import MQTTClient

global client_id


def connect_and_subscribe(mqtt_server, user, password):
    client_id = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, server=mqtt_server, user=user, password=password,port=1883,keepalive=30)
    client.connect()
    print(
        "Connected to %s MQTT broker, subscribed to %s topic"
        % (settings["mqtt_server"], settings["mqtt_topic"])
    )
    return client


def mqttrestart():
    print("Broker connection failure.")
    machine.reset()


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

        print("Initiating...")
        print("Calibrating...")
        mq2pinSignal = 34
        MQ2 = machine.ADC(machine.Pin(mq2pinSignal))  # define the analog input by sensor
        MQ2.atten(machine.ADC.ATTN_11DB)
        Ro = MQ2_data.MQCalibration(MQ2)
        print("Calibration is completed...")
        print("Ro={} kohm".format(Ro))

        station = network.WLAN(network.STA_IF)
        station.active(True)
        
        if not station.isconnected():
            station.connect(settings["ssid"], settings["password_wlan"])  # Connect to an AP

        while not station.isconnected():
            time.sleep(0.1)
        print("Connected to the wlan network")
        print(station.ifconfig())

       
        try:
            print("Connecting to mqttserver")
            client = connect_and_subscribe(
                settings["mqtt_server"],
                settings["mqtt_user"],
                settings["mqtt_password"],
                )
        except Exception as e:
            print("An error has occurred: {}".format(e))
            
        print("Connection successful")
        

        while True:
            message = get_data(MQ2, Ro)
            print(message)
            try:
                client.publish(settings["mqtt_topic"], message.encode("utf-8"))
            except:
                try:
                    print("Connecting to mqttserver")
                    client = connect_and_subscribe(settings["mqtt_server"],
                                                   settings["mqtt_user"],
                                                   settings["mqtt_password"]
                                                   )
                except Exception as e:
                    print("An error has occurred: {}".format(e))
                    mqttrestart()
                    pass
            time.sleep(5)
    except KeyboardInterrupt as e:
        print(e)
        print("Flashmode...")