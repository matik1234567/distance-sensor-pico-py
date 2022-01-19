from machine import Pin
import utime
import _thread

pulse = Pin(7, Pin.OUT)
receiver = Pin(13, Pin.IN, Pin.PULL_DOWN)

redLed1 = Pin(16, Pin.OUT)
greenLed1 = Pin(17, Pin.OUT)
redLed2 = Pin(18, Pin.OUT)
greenLed2 = Pin(12, Pin.OUT)

sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)
SpeedOfSound = 0.344
reading = sensor_temp.read_u16() * conversion_factor
temperature = 27 - (reading - 0.706)/0.001721

#matrix keypad init
col_list=[19,20,21]
row_list=[22,26,27,28]
for x in range(0,4):
    row_list[x]=Pin(row_list[x], Pin.OUT)
    row_list[x].value(1)

for x in range(0,3):
    col_list[x] = Pin(col_list[x], Pin.IN, Pin.PULL_UP)

key_map=[["#","0","*"],\
        ["9","8","7"],\
        ["6","5","4"],\
        ["3","2","1"]]

MIN_GREEN = 0
MIN_BOTH = 0
MIN_NONE = 0
MIN_RED = 0

GREEN = False
RED = False
PULSE = False
PULSE_FREQUENCY = 0
PROGRAMMING = False
TEMP_DISPLAY = False

def readSettings():
    global MIN_GREEN, MIN_BOTH, MIN_NONE, MIN_RED
    print("load settings")
    file = open("settings.txt","r+")
    lines = file.readlines()
    MIN_GREEN = float(lines[0][:-1])
    MIN_BOTH = float(lines[1][:-1])
    MIN_NONE = float(lines[2][:-1])
    MIN_RED = float(lines[3][:-1])
    print(MIN_GREEN, MIN_BOTH, MIN_NONE, MIN_RED)
    file.close()
    
def saveSettings(values):
    print("save settings")
    f = open("settings.txt","w")
    f.close()
    file = open("settings.txt","w+")
    new_settings = []
    for v in values:
        str_value = ""
        for n in v:
            str_value += str(n)
        new_settings.append(str_value)
    for s in new_settings:
        file.write(s+"\n")
    file.close()
    readSettings()
    
def getCurrentTemp():
    global sensor_temp, conversion_factor
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    return temperature

def computeDistance():
    pulse.low()
    utime.sleep_us(20)
    pulse.high()
    utime.sleep_us(10)
    pulse.low()
    exitLoop = False
    loopcount = 0
    delaytime = 0
    receivetime = 0
    
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
        
    if exitLoop == True: #signal failed
        return 0
    else:
        distance = ((receivetime - delaytime) * SpeedOfSound) / 2
        return distance / 10

def ledThread():
    global GREEN, RED, PULSE, PULSE_FREQUENCY, green_led, red_led, TEMP_DISPLAY, PROGRAMMING
    while True:
        if PROGRAMMING:
            redLed1.low()
            redLed2.low()
            greenLed1.low()
            utime.sleep_ms(1000)
            continue
        else:
            freq = int(PULSE_FREQUENCY)
            if RED:
                if PULSE:
                    redLed1.high()
                    redLed2.high()
                    utime.sleep_ms(freq)
                    redLed1.low()
                    redLed2.low()
                    utime.sleep_ms(freq)
                else:
                     redLed1.high()
                     redLed2.high()
            else:
                redLed1.low()
                redLed2.low()
            if GREEN:
                if PULSE:
                    greenLed1.high()
                    greenLed2.high()
                    utime.sleep_ms(freq)
                    greenLed1.low()
                    greenLed2.low()
                    utime.sleep_ms(freq)
                else:
                     greenLed1.high()
                     greenLed2.high()
            else:
                greenLed1.low()
                greenLed2.low()
                

def keypadRead(cols,rows):
    for r in rows:
        r.value(0)
        result=[cols[0].value(),cols[1].value(),cols[2].value()]
        if min(result)==0:
            key=key_map[int(rows.index(r))][int(result.index(0))]
            r.value(1) # manages key keept pressed
            return(key)
        r.value(1)
    
def programmingMode():
    global PROGRAMMING, greenLed2
    PROGRAMMING = True
    utime.sleep_ms(500)
    greenLed2.high()
    utime.sleep_ms(500)
    greenLed2.low()
    readValue = False
    valuesTemp = []
    valuesReal = []
    valuesCount = 0
    while True:
        if valuesCount == 4:
            break
        key=keypadRead(col_list, row_list)
        if key != None:
            readValue = True
            greenLed2.high()
            readKey = key
        else:
            if readValue:
                if readKey == '#':
                    valuesCount += 1
                    valuesReal.append(valuesTemp.copy())
                    valuesTemp.clear()
                else:
                    valuesTemp.append(readKey)
            readValue = False
            greenLed2.low()
        utime.sleep_ms(50)
    print(valuesReal)
    saveSettings(valuesReal)
    for i in range(0, 3):
        greenLed2.high()
        utime.sleep_ms(200)
        greenLed2.low()
        utime.sleep_ms(200)
    PROGRAMMING = False

#init program parameters
readSettings()
_thread.start_new_thread(ledThread, ())

while True:
    key=keypadRead(col_list, row_list)
    if key != None:
        if key == '*':
            programmingMode()
    
    distance = computeDistance()
    print(distance)
    PULSE_FREQUENCY = (distance*10) / 4
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
    utime.sleep_ms(300)
