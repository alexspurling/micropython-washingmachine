import time

import math
from micropython import const
from machine import Pin, ADC

RGB_LED_PIN = const(48)
LED_PIN = const(34)
BATTERY_PIN = 10


def update(existing_aggregate, new_value):
    (count, mean, M2) = existing_aggregate
    count += 1
    delta = new_value - mean
    mean += delta / count
    delta2 = new_value - mean
    M2 += delta * delta2
    return (count, mean, M2)


def finalize(existing_aggregate):
    (count, mean, M2) = existing_aggregate
    if count < 2:
        return float("nan")
    else:
        (mean, variance, sample_variance) = (mean, M2 / count, M2 / (count - 1))
        return (mean, variance, sample_variance)


def get_battery_voltage():

    # Returns the current battery voltage.
    # adc1 = ADC(Pin(BATTERY_PIN))  # Assign the ADC pin to read
    # We need to attenuate the input voltage so that we can read the full 0-3.3V range
    # adc1.atten(ADC.ATTN_11DB)
    # for _ in range(10):
    #     adc1.read()

    # adc1_value = adc1.read()
    # voltage1 = adc1_value / 4096 * 3.3
    # s3voltage = voltage1 / (422000 / (160000 + 422000))
    # return s3voltage

    # Assign the ADC pin to read
    adc = ADC(Pin(BATTERY_PIN))
    # We need to attenuate the input voltage so that we can read the full 0-3.3V range
    adc.atten(ADC.ATTN_11DB)

    num_samples = 16
    total_adc = 0
    for x in range(num_samples):
        total_adc += adc.read()

    adc_value = total_adc / num_samples

    voltage = adc_value / 4096 * 3.3
    wakeboard_voltage = voltage * 2  # Our voltage divider uses two 470k resistors to divide the value by two
    wakeboard_voltage += 0.185  # For some reason we tend to measure a voltage that is too low by about this much
    return adc_value, wakeboard_voltage


def get_battery_percentage():

    adc_value, battery_voltage = get_battery_voltage()

    # voltage divider uses 100k / 330k ohm resistors
    # 4.3V -> 3.223, 2.4 -> 1.842
    # expected_max = 4.3*330/(100+330)
    # expected_min = 2.8*330/(100+330)

    # BeeS3 measured resistances:
    # R1 = 161K  (code 164)
    # R2 = 390K (code 61D seems to refer to 422K so bit confused about this)

    # BeeS3 spec resistances:
    # R1 = 442K
    # R2 = 160K

    expected_max = 4.2
    expected_min = 3.1

    battery_level = (battery_voltage - expected_min) / (expected_max - expected_min)
    battery_percentage = max(min(battery_level * 100.0, 100), 0)
    return adc_value, battery_percentage, battery_voltage

