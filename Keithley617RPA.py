import pyvisa as visa
import time
import os
import csv
import matplotlib.pyplot as plt

rm = visa.ResourceManager()
rm.list_resources()
keithley = rm.open_resource('GPIB0::27::INSTR')

print("\nKeithley 617 RPA")
print("\n")
print("\nTakes in voltage bounds, step size and current measurement duration to direct the Keithley 617 Electrometer to aquire measurements of current over a swept range of voltages. Designed for use with an RPA.")

def AquireMaxInputs():
    print("\n")
    Resistance1 = input("\nResistance (in Ohms) >>")
    Resistance = float(Resistance1)
    MaxVoltage1 = input("\nMaximum voltage (in V) >> ")
    MaxVoltage = float(MaxVoltage1)
    MaxCurrent = abs(MaxVoltage/Resistance)
    return Resistance,MaxVoltage,MaxCurrent

def AquireMinInputs():
    MinVoltage1 = input("\nMinimum voltage >> ")
    MinVoltage = float(MinVoltage1)
    MinCurrent = abs(MinVoltage/Resistance)
    return MinVoltage,MinCurrent

def setVoltage(voltage):
    keithley.write("V" + "%.2f" % voltage + "X")

def currentMode():
    keithley.write("F1X")

def VsourceMode():
    keithley.write("O1X")

def VsourceOff():
    keithley.write("O0X")

date = input("\nInput the date (MM.DD.YYYY) >> ")

a = 0
while a == 0:
    Resistance,MaxVoltage,MaxCurrent = AquireMaxInputs()
    if MaxCurrent > 0.0015 or MaxVoltage > 100:
        print("\n")
        print("\n>>>WARNING<<<")
        print("\nCurrent inputs would result in a current exceeding 1.5 mA or the voltage exceeds 100 V, exceeding 2.0 mA and/or 100 V could damage the Keithley 617.")
        print("\nResistance = " + str(Resistance) + " ohms")
        print("Min voltage = " + str(MaxVoltage) + " V")
        print("Min current = " + str(MaxCurrent*1000) + " mA")
        print("\n")
        print("\nWould you like to proceed or change inputs?")
        choice = input("\n Enter 'P' for Proceed or 'C' for Change inputs >> ")
        if choice == "C":
            print("\nChanging inputs.")
        elif choice == "P":
            print("\nProceeding.")
            a = 1
        else:
            print("\nInvalid response. Changing inputs.")
        #end if
    else:
        a = 1
    #end if
#end while

b = 0
while b == 0:
    MinVoltage,MinCurrent = AquireMinInputs()
    if MinCurrent > 0.0015 or MinVoltage < -100:
        print("\n")
        print("\n>>>WARNING<<<")
        print("\nCurrent inputs would result in a current exceeding 1.5 mA or the voltage exceeds 100 V, exceeding 2.0 mA and/or 100 V could damage the Keithley 617.")
        print("\nResistance = " + str(Resistance) + " ohms")
        print("Min voltage = " + str(MinVoltage) + " V")
        print("Min current = " + str(MinCurrent*-1000) + " mA")
        print("\n")
        print("\nWould you like to proceed or change inputs?")
        choice = input("\n Enter 'P' for Proceed or 'C' for Change inputs >> ")
        if choice == "C":
            print("\nChanging inputs.")
        elif choice == "P":
            print("\nProceeding.")
            b = 1
        else:
            print("\nInvalid response. Changing inputs.")
        #end if
    else:
        b = 1
    #end if
#end while

StepVoltage1 = input("\nVoltage step size (V) >> ")
StepVoltage = float(StepVoltage1)
deltaT1 = input("\nMeasurement duration (s) >> ")
deltaT = float(deltaT1)
stepDelay = 0.34

print("\n")
print("\nResistance: ")
print(str(Resistance) + " ohms.")
print("\n")
print("\nVoltage Range: ")
print(str(MinVoltage) + " V - " + str(MaxVoltage) + " V, stepping " + str(StepVoltage) + " V.")
print("\n")
print("\nExpected Current Range: ")
print(str(MinCurrent*-1000) + " mA - " + str(MaxCurrent*1000) + " mA.")
print("\n")
print("\nCurrent Measurement Duration: ")
print(str(deltaT) + " seconds.")

c = 0
while c == 0:
    print("\n")
    ready = input("\nCommence with measurement? (Y/n) >> ")
    if ready == "Y":
        print("\nCommencing.")
        c = 1
    elif ready == "n":
        print("\nMeasurement cancelled. Exiting code.")
        raise ValueError("\nFailure due to user input.")
    else:
        print("\nInvalid response.")
    #end if
#end while

voltageNow = MinVoltage
voltage = []
current = []
mAcurrent = []

t = 0

VsourceMode()
currentMode()
while voltageNow <= MaxVoltage:

    setVoltage(voltageNow)
    tempCurrents = []

    if t == 0:
        time.sleep(10)
    else:
        time.sleep(2)
    #end if

    startTime = time.time()
    while deltaT > (time.time() - startTime):
        tempCurrents.append(keithley.read())
        time.sleep(stepDelay - ((time.time()-startTime)%stepDelay))
    #end while

    numMeas = len(tempCurrents)
    i = 0
    total = 0

    while i < numMeas:
        tempCurrents[i] = (tempCurrents[i][4:])
        total = total + float(tempCurrents[i])
        i = i + 1
    #end while

    Iavg = total/numMeas

    if Iavg >= 0.002:
        VsourceOff()
        print("\n2mA EXCEEDED. TURNING OFF VOLTAGE SOURCE AND HALTING PROGRAM.")
        raise ValueError("\nCurrent limit exceeded.")
    #end if

    voltage.append(voltageNow)
    current.append(Iavg)
    mAcurrent.append(Iavg*1000)
    print("\n")
    print("Voltage = " + str(voltageNow) + " V, Current = " + str(Iavg*1000) + " mA.")
    t = t + 1
    voltageNow = voltageNow + StepVoltage
#end while

VsourceOff()

MYDIR = "C:\\Users\\Elijah\\Downloads\\RPATests\\"
MYDIR = os.path.expanduser(MYDIR)

if MinVoltage < 0:
    absMinVoltage = abs(MinVoltage)
    Placeholder = "R" + str(Resistance) + "Vneg" + str(absMinVoltage) + "_" + str(MaxVoltage) + "step" + str(StepVoltage)
else:
    Placeholder = "R" + str(Resistance) + "V" + str(MinVoltage) + "_" + str(MaxVoltage) + "step" + str(StepVoltage)
#end if

Filename = date + "%sData.csv" % (Placeholder)
path = MYDIR + Filename

with open (path,'w', newline = '') as f:
    writer = csv.writer(f)
    writer.writerow(voltage)
    writer.writerow(current)
#end with

plotTitle = input("\nInput Chart Title >> ")

x = voltage
y = mAcurrent

plt.plot(x,y)
plt.xlabel("Voltage (V)")
plt.ylabel("Current (mA)")
plt.title(plotTitle)
plt.show()