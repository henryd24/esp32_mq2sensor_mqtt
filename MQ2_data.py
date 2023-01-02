import math
import time

global RL_VALUE, CH4, MQ2, RO_CLEAN_AIR_FACTOR, CALIBRATION_SAMPLE_TIMES, CALIBRATION_SAMPLE_INTERVAL, READ_SAMPLE_INTERVAL, READ_SAMPLE_TIMES, GAS_CH4, GAS_PROPANE, CH4Curve, PROPANECurve
global GAS_SMOKE, GAS_CO, GAS_LPG
# ************************************************************************************
RL_VALUE = 10  # defines the value of the load resistance in kilo ohms.
RO_CLEAN_AIR_FACTOR = 9.83  # sensor resistance in the clean air / RO, which is derived from the table in the data sheet
# ************************************************************************************
CALIBRATION_SAMPLE_TIMES = (
    100  # define how many samples you will take in the calibration phase
)
CALIBRATION_SAMPLE_INTERVAL = 100  # defines the time interval (in milliseconds) between each sample in the calibration phase
READ_SAMPLE_INTERVAL = 50  # define how many samples you are going to take in a normal operation
READ_SAMPLE_TIMES = 5  #defines the time interval (in milliseconds) between each sample in a normal operation.
# ************************************************************************************
GAS_CH4 = 0
GAS_PROPANE = 1
GAS_SMOKE = 2
GAS_CO = 3
GAS_LPG = 4
# ************************************************************************************
CH4Curve = [2.3, 0.47, -0.37]  # two points are taken from the curve.
# with these two points, a line is formed which is "approximately equivalent"
# to the original curve.
# data format:{ x, y, slope}; point1: (lg200, 0.47), point2: (lg10000, -0.16)
PROPANECurve = [2.3, 0.23, -0.47]  # same
# data format:{ x, y, slope}; point1: (lg200, 0.23), point2: (lg10000, -0.-57)
SmokeCurve = [2.3, 0.53, -0.44]
COCurve = [2.3, 0.72, -0.34]
LPGCurve = [2.3, 0.21, -0.47]
Ro = 10
# ****************** MQResistanceCalculation *****************************************
# Input:   raw_adc - raw value read from adc, which represents the voltage
# Output:  the calculated sensor resistance
# Remarks: The sensor and the load resistor forms a voltage divider. Given the voltage
#         across the load resistor and its resistance, the resistance of the sensor
#         could be derived.
# ************************************************************************************
def MQResistanceCalculation(raw_adc):
    return RL_VALUE * (1024 - raw_adc) / raw_adc
    # ************************************************************************************
    # ***************************** MQCalibration ****************************************
    # Input:   mq_pin - analog channel
    # Output:  Ro of the sensor
    # Remarks: This function assumes that the sensor is in clean air. It use
    #         MQResistanceCalculation to calculates the sensor resistance in clean air
    #         and then divides it with RO_CLEAN_AIR_FACTOR. RO_CLEAN_AIR_FACTOR is about
    #         10, which differs slightly between different sensors.
    # ************************************************************************************


def MQCalibration(mq_pin):
    val = 0
    for i in range(CALIBRATION_SAMPLE_TIMES):
        val += MQResistanceCalculation(mq_pin.read())
        time.sleep(CALIBRATION_SAMPLE_INTERVAL / 1000)
    val = val / CALIBRATION_SAMPLE_TIMES  # calculate the average value
    val = (
        val / RO_CLEAN_AIR_FACTOR
    )  # divided by RO_CLEAN_AIR_FACTOR yields the Ro according to the chart in the datasheet
    return val
    # *****************************  MQRead *********************************************
    # Input:   mq_pin - analog channel
    # Output:  Rs of the sensor
    # Remarks: This function use MQResistanceCalculation to caculate the sensor resistenc (Rs).
    #         The Rs changes as the sensor is in the different consentration of the target
    #         gas. The sample times and the time interval between samples could be configured
    #         by changing the definition of the macros.
    # ************************************************************************************


def MQRead(mq_pin):
    rs = 0
    for i in range(READ_SAMPLE_TIMES):
        rs += MQResistanceCalculation(mq_pin.read())
        time.sleep(READ_SAMPLE_INTERVAL / 1000)
    rs = rs / READ_SAMPLE_TIMES
    return rs
    # *****************************  MQGetPercentage **********************************
    # Input:   rs_ro_ratio - Rs divided by Ro
    #         pcurve      - pointer to the curve of the target gas
    # Output:  ppm of the target gas
    # Remarks: By using the slope and a point of the line. The x(logarithmic value of ppm)
    #         of the line could be derived if y(rs_ro_ratio) is provided. As it is a
    #         logarithmic coordinate, power of 10 is used to convert the result to non-logarithmic
    #         value.
    # ************************************************************************************


def MQGetPercentage(rs_ro_ratio, pcurve):
    try:
        return math.pow(
            10, (((math.log(rs_ro_ratio) - pcurve[1]) / pcurve[2]) + pcurve[0])
        )
    except:
        return 402
    # *****************************  MQGetGasPercentage **********************************
    # Input:   rs_ro_ratio - Rs divided by Ro
    #         gas_id      - target gas type
    # Output:  ppm of the target gas
    # Remarks: This function passes different curves to the MQGetPercentage function which
    #         calculates the ppm (parts per million) of the target gas.
    # ************************************************************************************


def MQGetGasPercentage(rs_ro_ratio, gas_id):
    if gas_id == GAS_CH4:
        return MQGetPercentage(rs_ro_ratio, CH4Curve)
    elif gas_id == GAS_PROPANE:
        return MQGetPercentage(rs_ro_ratio, PROPANECurve)
    elif gas_id == GAS_SMOKE:
        return MQGetPercentage(rs_ro_ratio, SmokeCurve)
    elif gas_id == GAS_CO:
        return MQGetPercentage(rs_ro_ratio, COCurve)
    elif gas_id == GAS_LPG:
        return MQGetPercentage(rs_ro_ratio, LPGCurve)
