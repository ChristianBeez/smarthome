from astral import LocationInfo
from astral.sun import sun
from datetime import date, datetime, timedelta
from time import sleep
import pytz
from modbus import *

global client

city = LocationInfo(name="Haig", region="Germany", timezone="Europe/Berlin", latitude=50.28499, longitude=11.27749)

def getRise():
    s = sun(city.observer, tzinfo=city.timezone)
    sunrise = s["sunrise"]
    print('Sonnenaufgang')
    print(sunrise)
    return(sunrise)
    
def getSet():
    s = sun(city.observer, tzinfo=city.timezone)
    dusk = s["dusk"]
    sset = s["sunset"]
    sunset = sset + timedelta(seconds = (dusk - sset).total_seconds() / 2.2)
    print('dusk')
    print(dusk)
    print('sunset')
    print(sset)
    print('Errechnet')
    print(sset + timedelta(seconds = (dusk - sset).total_seconds() / 2.2))
    print('aktuell')
    print(sunset)
    return(sunset)

def getbeforeDark():
    s = sun(city.observer, tzinfo=city.timezone)
    sset = s["sunset"]
    sunset = sset + timedelta(minutes = 5)
    return(sunset)


sunrise = getRise()
sunset = getSet()
beforeDark = getbeforeDark()
sleept = datetime.now(pytz.timezone('Europe/Berlin')).replace(hour=22,minute=0,second=0,microsecond=0)
tempDay = True
tempNight = True
tempDark = True
tempSleept = True
tempSchlafRollo = True
SchlafRollo = False ## Wenn True eingestellt, fährt der Schlafzimmer-Rollo eine Stunde vor Sonnenaufgang herunter
christmas = False ## an Weichnachten wird die Lichterkette und außen über die Balkonsteckdose gesteuert
extremeHot = False ## Wenn es total Warm ist (True), müssen die Rollos offen bleiben, damit kalt gelüftet werden kann

while True:
    utc=pytz.UTC
    time_now = datetime.now(pytz.timezone('Europe/Berlin'))  ##utc.localize(datetime.now())
    
    if sunrise.date() != time_now.date():
        print('Daten werden aktuallisiert')
        sunrise = getRise()
        sunset = getSet()
        beforeDark = getbeforeDark()
        sleept = datetime.now(pytz.timezone('Europe/Berlin')).replace(hour=22,minute=0,second=0,microsecond=0)
        tempDay = True
        tempNight = True
        tempDark = True
        tempSleept = True
        tempSchlafRollo = True
        

    if time_now > sunrise and time_now < sunset and tempDay == True and extremeHot == False: # bin ich zwischen Sonnenaufgang und Abenddämmerung?
        print("Es ist Tag")
        print(time_now)
        
        client = connectMod()
        if client == 0:
            continue
        else:
            ret = '0'
            regist = readRegister(client)
            if regist == 0:
                continue
            else:
                dig = createDig(regist)
                out = createList()
                lval = ['Kueche','Wohnzimmer','Kind1','Kind2','BadOG','BadDG']
                handle(dig, lval, 'auf', out)
                write(client,out)
                disconnectMod(client)
                tempDay = False
            
    elif time_now > sunset and tempNight == True and extremeHot == False: 
        print("es ist Nacht")
        print(time_now)
        
        client = connectMod()
        if client == 0:
            continue
        else:
            ret = '0'
            regist = readRegister(client)
            if regist == 0:
                continue
            else:
                dig = createDig(regist)
                out = createList()
                lval = ['Kueche','Wohnzimmer','Kind1','Kind2','BadOG']
                handle(dig, lval, 'zu', out)
                write(client,out)
                disconnectMod(client)
                tempNight = False
    
    # Das hier schaltet die Lichterkette für Weihnachten. 
    if time_now > beforeDark and time_now < sleept and tempSleept == True and christmas == True: 
        print("es wird bald Dunkel")
        print(time_now)
        client = connectMod()
        
        if client == 0:
            continue
        else:
            ret = '0'
            regist = readRegister(client)
            if regist == 0:
                continue
            else:
                dig = createDig(regist)
                out = createList()
                lval = ['BalkonSteckdose']
                handle(dig, lval, 'ein', out)
                write(client,out)
                disconnectMod(client)
                tempSleept = False
            
    elif time_now > sleept and tempDark == True and christmas == True:
        print("es ist Nacht")
        print(time_now)
        client = connectMod()
        
        if client == 0:
            continue
        else:
            ret = '0'
            regist = readRegister(client)
            if regist == 0:
                continue
            else:
                dig = createDig(regist)
                out = createList()
                lval = ['BalkonSteckdose']
                handle(dig, lval, 'aus', out)
                write(client,out)
                disconnectMod(client)
                tempDark = False
            
            
    if time_now > sunrise - timedelta(seconds = 3600) and tempSchlafRollo == True and SchlafRollo == True: # Schlafzimmerrollo fährt herunter
        print("Eine Stunde vor Sonnenaufgang")
        print(time_now)
        
        client = connectMod()
        if client == 0:
            continue
        else:
            ret = '0'
            regist = readRegister(client)
            if regist == 0:
                continue
            else:
                dig = createDig(regist)
                out = createList()
                lval = ['Schlafzimmer']
                handle(dig, lval, 'zu', out)
                write(client,out)
                disconnectMod(client)
                tempSchlafRollo = False
        
    time.sleep(60)
