from machine import Pin
import utime
import _thread


pulse = Pin(26, Pin.OUT)
receiver = Pin(18, Pin.IN, Pin.PULL_DOWN)
red_led = Pin(15, Pin.OUT)
green_led = Pin(14, Pin.OUT)
yellow_led = Pin(19, Pin.OUT)
button = Pin(2, Pin.IN, Pin.PULL_DOWN)

sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)
#SpeedOfSound = 331.5
SpeedOfSound = 0.344
reading = sensor_temp.read_u16() * conversion_factor
temperature = 27 - (reading - 0.706)/0.001721


MIN_GREEN = 1500.0
MIN_BOTH = 400.0
MIN_NONE = 300.0
MIN_RED = 0.0

GREEN = False
RED = False
PULSE = False
PULSE_FREQUENCY = 0
PROGRAMMING = False

yellow_led.low()
green_led.low()
red_led.low()

def getCurrentTemp():
    global sensor_temp, conversion_factor
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    return temperature

def pulseShort():
    global yellow_led
    yellow_led.high()
    utime.sleep_ms(200)
    yellow_led.low()
    utime.sleep_ms(1000)

def pulseLong():
    global yellow_led
    yellow_led.high()
    utime.sleep_ms(1000)
    yellow_led.low()
    utime.sleep_ms(1000)

TEMP_DISPLAY = False
def displayMorseTemperature():
    global TEMP_DISPLAY
    if TEMP_DISPLAY:
        return
    TEMP_DISPLAY = True
    temp_str = str(round(getCurrentTemp(), 1))
    print(temp_str)
    #code
    for num in temp_str:
        if num == '.':
            continue
        else:
            num_i = int(num)
            if num_i <= 5:
                for i in range(0, 5):
                    if i < num_i:
                        pulseShort()
                    else:
                        pulseLong()
            else:
                for i in range(0, 5):
                    if i < num_i - 5:
                        pulseLong()
                    else:
                        pulseShort()
                    
    
    #end code
    TEMP_DISPLAY = False

    
def computeDistance():
    pulse.low()
    utime.sleep_us(20)
    pulse.high()
    utime.sleep_us(10)
    pulse.low()
    exitLoop = False
    loopcount = 0
    while receiver.value() == 0 and exitLoop == False:
        loopcount = loopcount + 1
        delaytime = utime.ticks_us()
        if loopcount > 3000:
            exitLoop == True
    while receiver.value() == 1 and exitLoop == False:
        loopcount = loopcount + 1
        receivetime = utime.ticks_us()
        if loopcount > 3000:
            exitLoop == True
        
    if exitLoop == True:
        return 0
    else:
        #distance = ((receivetime - delaytime) * ((SpeedOfSound + (0.6 * temperature)) / 1000)) / 2
        distance = ((receivetime - delaytime) * SpeedOfSound) / 2
        return distance

def ledThread():
    global GREEN, RED, PULSE, PULSE_FREQUENCY, green_led, red_led, PROGRAMMING
    while True:
        if PROGRAMMING:
            utime.sleep_ms(1000)
            continue
        if TEMP_DISPLAY:
            green_led.low()
            red_led.low()
            utime.sleep_ms(1000)
        else:
            freq = int(PULSE_FREQUENCY)
            if RED:
                if PULSE:
                    red_led.high()
                    utime.sleep_ms(freq)
                    red_led.low()
                    utime.sleep_ms(freq)
                else:
                     red_led.high()
            else:
                red_led.low()
            if GREEN:
                if PULSE:
                    green_led.high()
                    utime.sleep_ms(freq)
                    green_led.low()
                    utime.sleep_ms(freq)
                else:
                     green_led.high()
            else:
                green_led.low()

_thread.start_new_thread(ledThread, ())

def get_digit(num):
    is_first = False
    count = 0
    for n in range(0,  len(num)):
        if n == 0  and num[0] == 0:
            is_first = True
        if is_first:
            if num[n] == 0:
                count += 1
            else:
                return count
        else:
            if num[n] == 1:
                count += 1
            else:
                if count == 5:
                    return 0
                else:
                    count += 5
                    return count
    return 0
                
def programming():
    global PROGRAMMING
    PROGRAMMING = True
    digits_count = 0
    inputs = 0
    long = False
    short = False
    oninput = False
    utime.sleep_ms(1500)
    green_led.low()
    red_led.low()
    yellow_led.high()
    nums = []
    num = []
    button_start = False
    if button.value():
        button_start = True
    while digits_count < 3:
        if button_start:
            if not button.value():
                button_start = False
            continue
        if button.value():
            oninput = True
            if not short:
                short = True
                green_led.high()
            else:
                long = True
                red_led.high()
        elif oninput:
            oninput = False
            if long:
                print('long')
                num.append(1)
            else:
                print('short')
                num.append(0)
            long = False
            short = False
            inputs += 1
            green_led.low()
            red_led.low()
            if inputs == 5:
                digits_count += 1
                inputs = 0
                nums.append(get_digit(num))
                print(nums)
                yellow_led.low()
                utime.sleep_ms(500)
                yellow_led.high()
                utime.sleep_ms(500)
                yellow_led.low()
                utime.sleep_ms(500)
                yellow_led.high()
                num.clear()
        utime.sleep_ms(1000)
    yellow_led.low()
    PROGRAMMING = False
            
while True:
    if button.value():
        utime.sleep_ms(500)
        if button.value():
            print('programming')
            programming()
        else:
            displayMorseTemperature()
    elif TEMP_DISPLAY == False:
        distance = computeDistance()
        # print(distance, GREEN, RED, PULSE)
        PULSE_FREQUENCY = distance / 4
        if distance > MIN_GREEN:
            GREEN = True
            RED = False
            PULSE = False
        elif distance <= MIN_GREEN and distance > MIN_BOTH:
            GREEN = True
            RED = True
            PULSE = True
        elif distance <= MIN_BOTH and distance > MIN_NONE:
            GREEN = False
            RED = False
        elif distance <= MIN_NONE and distance > MIN_RED:
            GREEN = False
            RED = True
            PULSE = False
    utime.sleep_ms(400)
