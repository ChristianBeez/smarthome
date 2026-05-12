import logging
import os
import time
import random
import urllib.request
import ssl
import json

from flask import Flask, request, jsonify, render_template
from flask_ask import Ask, request, session, question, statement
from modbus import *

UNNUETZES_WISSEN = [
    # Tiere
    "Schmetterlinge schmecken mit ihren Füßen.",
    "Ein Oktopus hat drei Herzen.",
    "Schnecken können bis zu drei Jahre schlafen.",
    "Kängurus können nicht rückwärts laufen.",
    "Würmer haben fünf Herzen.",
    "Flamingos sind nicht von Natur aus pink – sie färben sich durch ihre Nahrung.",
    "Elefanten sind die einzigen Säugetiere, die nicht springen können.",
    "Kühe haben beste Freunde und werden gestresst, wenn sie getrennt werden.",
    "Delfine schlafen mit einem Auge offen.",
    "Ein Eichhörnchen vergisst bis zu 50 Prozent seiner versteckten Nüsse.",
    "Tintenfische haben blaues Blut.",
    "Hummern können biologisch nicht altern.",
    "Pinguine machen ihren Partnerinnen einen Heiratsantrag mit einem Kieselstein.",
    "Krokodile können ihre Zunge nicht herausstrecken.",
    "Haie sind älter als Bäume.",
    "Seeotter halten beim Schlafen Händchen, damit sie nicht auseinandertreiben.",
    "Libellen haben eine Trefferquote bei der Jagd von 95 Prozent.",
    "Ein Nashorn-Horn besteht aus gepresstem Haar.",
    "Gorillas können Sonnenbrand bekommen.",
    "Erdmännchen sind immun gegen manche Schlangengifte.",
    "Bienen fliegen bei Regen unter Blättern, um trocken zu bleiben.",
    "Das Brummen einer Katze kann die Knochenheilung fördern.",
    "Fische können ertrinken, wenn das Wasser zu wenig Sauerstoff hat.",
    "Eine Gruppe Katzen heißt Clowder.",
    "Schafe haben einen Blickwinkel von 270 Grad, ohne den Kopf zu drehen.",
    "Bienen können Menschengesichter erkennen und wiedererkennen.",
    "Eine Schnecke hat bis zu 25.000 Zähne.",
    "Männliche Seepferdchen tragen und gebären die Jungen.",
    "Ameisen schlafen etwa acht Stunden täglich – in kurzen Nickerchen.",
    "Kaninchen können vor Freude einen Herzinfarkt bekommen.",
    "Kühe machen regionale Dialekte beim Muhen.",
    "Ein Schimpanse ist stärker als fünf ausgewachsene Menschen.",
    "Flamingos können nur fressen, wenn ihr Kopf nach unten hängt.",
    "Spinnen segeln durch die Luft, indem sie Fäden im Wind nutzen.",
    "Papageien können Werkzeug benutzen.",
    # Menschlicher Körper
    "Der menschliche Körper enthält genug Fett für sieben Stück Seife.",
    "Dein Gehirn ist aktiver, wenn du schläfst, als wenn du fernsehst.",
    "Jeder Mensch hat einen einzigartigen Zungenabdruck.",
    "Knochen sind viermal so stark wie Beton.",
    "Das Ohr hört niemals auf zu hören – auch im Schlaf.",
    "Menschen sind die einzigen Tiere mit einem Kinn.",
    "Die Nase kann über eine Billion verschiedene Gerüche unterscheiden.",
    "Das menschliche Gehirn verbraucht 20 Prozent der gesamten Körperenergie.",
    "Jeder Mensch hat eine einzigartige Iris – auch eineiige Zwillinge.",
    "Die Leber kann sich selbst regenerieren.",
    "Du bist morgens etwa einen Zentimeter größer als abends.",
    "Das Herz schlägt im Leben eines Menschen etwa 2,5 Milliarden Mal.",
    "Menschen produzieren im Leben genug Speichel, um zwei Schwimmbecken zu füllen.",
    "Fingernägel wachsen schneller als Zehennägel.",
    "Das Auge kann 10 Millionen verschiedene Farben unterscheiden.",
    "Dein Körper hat mehr Bakterienzellen als menschliche Zellen.",
    "Du schließt deine Augen etwa 15 Mal pro Minute.",
    "Du wirst niemals dein eigenes Gesicht direkt sehen – nur Spiegelungen.",
    "Menschen sind die einzigen Tiere, die weinend schluchzen.",
    "Dein Gehirn verändert eine Erinnerung leicht, jedes Mal wenn du sie abrufst.",
    "Das Gehirn behandelt sozialen Schmerz ähnlich wie physischen Schmerz.",
    "Menschen können bis zu 5000 Gesichter erkennen und sich merken.",
    "Babys tanzen instinktiv zur Musik – bereits mit sieben Monaten.",
    "Das stärkste Organ im menschlichen Körper – gemessen am Gewicht – ist die Zunge.",
    "Dein Magen bekommt alle zwei Wochen eine neue Schleimhaut.",
    "Du kannst nicht niesen, ohne die Augen zu schließen.",
    # Wissenschaft & Weltall
    "Ein Tag auf der Venus ist länger als ein Jahr auf der Venus.",
    "Blitze sind fünfmal heißer als die Oberfläche der Sonne.",
    "Honig verdirbt nie – in Pyramiden gefundener Honig war noch essbar.",
    "Die Erde dreht sich pro Jahrhundert um 0,002 Sekunden langsamer.",
    "Der Mond entfernt sich jedes Jahr 3,8 Zentimeter von der Erde.",
    "Licht braucht 8 Minuten von der Sonne bis zur Erde.",
    "Es gibt mehr mögliche Schachspiele als Atome im beobachtbaren Universum.",
    "Diamanten können verbrennen.",
    "Der Weltraum ist absolut still – Schall kann sich im Vakuum nicht ausbreiten.",
    "Es gibt mehr Sterne im Universum als Sandkörner auf der Erde.",
    "Ein Teelöffel Neutronensternmaterie würde eine Milliarde Tonnen wiegen.",
    "Wasser kann gleichzeitig kochen und gefrieren – das nennt sich Tripelpunkt.",
    "Licht reist in einer Sekunde 7,5 Mal um die Erde.",
    "Die Sahara ist nicht die größte Wüste – die Antarktis ist eine Wüste.",
    "Der Himalaya wächst jedes Jahr um fünf Millimeter.",
    "Kanada hat mehr Seen als der Rest der Welt zusammen.",
    "Russland ist flächenmäßig größer als der Planet Pluto.",
    "Australien ist breiter als der Mond.",
    "Es gibt mehr leerstehende Häuser in Japan als Obdachlose.",
    "Amsterdam hat mehr Fahrräder als Einwohner.",
    # Geschichte
    "Napoleon war für seine Zeit durchschnittlich groß – 1,69 Meter.",
    "Kleopatra lebte zeitlich näher an der Mondlandung als am Bau der Pyramiden.",
    "Oxford University ist älter als die Azteken.",
    "Der erste Computerbug war ein echter Käfer – ein Falter steckte in einer Maschine.",
    "Das Fax wurde erfunden, bevor das Telefon erfunden wurde.",
    "Nintendo wurde 1889 als Spielkartenhersteller gegründet.",
    "Wikinger hatten keine gehörnten Helme – das ist ein Mythos.",
    "Die Berliner Mauer stand kürzer als Instagram existiert.",
    "Ein Krieg zwischen Honduras und El Salvador wurde durch ein Fußballspiel ausgelöst.",
    "Piratenflaggen dienten ursprünglich als Signal für einen fairen Kampf.",
    "Golf wurde als erstes auf dem Mond gespielt – von Astronaut Alan Shepard.",
    "Der erste Alarm-Wecker klingelte nur um 4 Uhr morgens.",
    "Mehr Menschen wurden statistisch von Kamelen getötet als von Haien.",
    "Das Schachspiel wurde in Indien erfunden, nicht in Europa.",
    "Die ersten Olympischen Spiele verboten Frauen sogar als Zuschauer.",
    # Essen & Trinken
    "Bananen sind leicht radioaktiv.",
    "Ketchup war früher als Medizin verschrieben.",
    "Erdnüsse sind keine Nüsse – sie sind Hülsenfrüchte.",
    "Ananas enthält ein Enzym, das langsam deine Zunge verdaut.",
    "Cashews wachsen außen an einer Frucht.",
    "Eine Banane ist botanisch gesehen eine Beere – eine Erdbeere nicht.",
    "Karotten waren ursprünglich lila, nicht orange.",
    "Koffein ist die weltweit meistkonsumierte psychoaktive Substanz.",
    "Kartoffeln wurden in Europa lange Zeit für giftig gehalten.",
    "Kühe geben mehr Milch, wenn sie Musik hören.",
    "Schokolade war bei den Azteken eine Währung.",
    "Weiße Schokolade enthält keine Kakaomasse – sie ist technisch keine Schokolade.",
    "Ein Liter Honig erfordert, dass Bienen zwei Millionen Blüten besuchen.",
    "Wasabi aus deutschen Restaurants ist meistens gefärbter Meerrettich.",
    "Zitronenlimonade enthält oft mehr Zucker als Cola.",
    # Technologie
    "Das erste Computerpasswort der Welt war 'password'.",
    "Das erste Handy wog 1,1 Kilogramm.",
    "E-Mails existierten vor dem Internet.",
    "Die QWERTY-Tastatur wurde entwickelt, um Schreibmaschinen zu verlangsamen.",
    "Ein modernes Smartphone hat mehr Rechenleistung als alle NASA-Computer bei der Mondlandung zusammen.",
    "Der erste Webserver der Welt ist noch aktiv.",
    "Der erste Videoanruf fand 1964 auf der New Yorker Weltmesse statt.",
    "Google wurde in einer Garage gegründet.",
    "Das erste iPhone hatte bei der Markteinführung nur vier Apps.",
    "YouTube wurde ursprünglich als Dating-Plattform geplant.",
    "Twitter-Gründer Jack Dorsey schickte den ersten Tweet an sich selbst.",
    "Amazon begann als Online-Buchhandlung – in einer Garage.",
    "Die erste Computermaus war aus Holz.",
    # Sprache & Wörter
    "Das Wort Ohrwurm ist ein deutsches Exportwort, das weltweit verwendet wird.",
    "Im Deutschen gibt es ein Wort für den Geruch nach Regen: Petrichor.",
    "In manchen Sprachen gibt es kein Wort für die Farbe Blau.",
    "Das Ausrufezeichen wurde als Freudenschrei der Römer erfunden.",
    "Es gibt über 3000 verschiedene Sprachen auf der Welt.",
    "Das Wort Quiz hat keinen lateinischen oder griechischen Ursprung.",
    "Schadenfreude ist ein deutsches Wort, das weltweit verwendet wird.",
    "Das Wort Kindergarten ist ein deutsches Exportwort.",
    "In Papua-Neuguinea werden über 800 verschiedene Sprachen gesprochen.",
    "Das Wort Zeitgeist wird weltweit im Original verwendet.",
    "Das kürzeste vollständige Satz im Deutschen ist: Geh.",
    # Alltag & Skurriles
    "Ein durchschnittlicher Mensch verbringt sechs Monate seines Lebens damit, auf rote Ampeln zu warten.",
    "85 Prozent aller Kugelschreiber enden ihr Leben nicht leer, sondern werden verloren.",
    "Mehr Monopoly-Geld wird pro Jahr gedruckt als echtes US-Dollar.",
    "IKEA besitzt mehr Wald als jedes andere Unternehmen der Welt.",
    "In der Schweiz ist es illegal, ein Meerschweinchen alleine zu halten.",
    "In England ist es verboten, eine Briefmarke mit dem Königsbild auf den Kopf zu kleben.",
    "Eine durchschnittliche Wolke wiegt etwa 500.000 Kilogramm.",
    "Die meisten Menschen träumen in Farbe – aber nicht alle.",
    "Du blinzelst seltener, wenn du auf einen Bildschirm schaust.",
    "Menschen sind schlechter im Multitasking als sie glauben – das Gehirn switcht nur schnell.",
    "Ein durchschnittlicher Mensch geht in seinem Leben dreimal um die Erde – zu Fuß.",
    "Menschen sind die einzigen Tiere, die freiwillig ins Feuer schauen.",
    "Das menschliche Gehirn kann keine Zeitdauer ohne äußere Referenz genau einschätzen.",
    "In Alaska ist es verboten, einem Elch Alkohol zu geben.",
    "Jeden Tag sterben mehr Menschen durch Kokosnüsse als durch Haie.",
    # Mathematik & Zahlen
    "111.111.111 mal 111.111.111 ergibt 12.345.678.987.654.321.",
    "Die Summe aller Zahlen von 1 bis 100 ist 5050.",
    "Pi enthält statistisch jede beliebige Zahlenfolge irgendwo.",
    "Eine Billion Sekunden entspricht etwa 31.710 Jahren.",
    "Wenn du ein Papier 42 Mal falten könntest, wäre es so dick wie die Entfernung zum Mond.",
    "Es gibt mehr mögliche Sudoku-Rätsel als Atome auf der Erde.",
    # Psychologie
    "Das Gehirn kann nicht unterscheiden, ob man wirklich lacht oder nur lacht – beide heben die Stimmung.",
    "Menschen erinnern sich besser an unvollendete Aufgaben als an abgeschlossene.",
    "Deja-vu ist wahrscheinlich ein kurzfristiger Speicherfehler im Gehirn.",
    "Farben beeinflussen den Appetit – deshalb sind Fast-Food-Logos oft rot und gelb.",
    "Menschen schätzen Dinge höher ein, für die sie gearbeitet haben – das nennt sich IKEA-Effekt.",
    "Wir treffen täglich bis zu 35.000 Entscheidungen – die meisten unbewusst.",
    "Langeweile macht kreativ – das Gehirn sucht aktiv nach Beschäftigung.",
    "Menschen überschätzen systematisch ihr eigenes Fachwissen.",
    # Musik
    "Happy Birthday war bis 2016 urheberrechtlich geschützt.",
    "Das Gehirn reagiert auf Musik ähnlich wie auf Essen oder soziale Belohnung.",
    "Gänsehaut bei Musik erleben nur etwa 50 Prozent der Menschen.",
    "Das langsamste Musikstück der Welt dauert 639 Jahre.",
    "Musik bei 60 Schlägen pro Minute synchronisiert sich mit dem menschlichen Herzschlag.",
    # Geld & Wirtschaft
    "Die erste Kreditkarte wurde 1950 eingeführt.",
    "Zwei Drittel des weltweiten Bargeldes befindet sich außerhalb der USA.",
    "Die reichsten 1 Prozent besitzen mehr als die anderen 99 Prozent zusammen.",
    # Sport
    "Der erste Marathonläufer bei den Olympischen Spielen trank unterwegs Cognac.",
    "Ein Baseball wird im Durchschnitt nach sechs Würfen ausgetauscht.",
    "Die schnellste je gemessene Tennisball-Geschwindigkeit war 263 Kilometer pro Stunde.",
    "Tischtennis wurde ursprünglich mit Champagnerkorken und Büchern gespielt.",
    "Beim ersten Fußball-WM-Finale 1930 wurde der Ball jeder Mannschaft für eine Halbzeit verwendet.",
]

def get_random_response():
    """Zufällig ein Witz von JokeAPI oder ein unnützes Wissen aus der lokalen Liste."""
    if random.choice(['joke', 'fakt']) == 'fakt':
        return random.choice(UNNUETZES_WISSEN)
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kategorie = random.choice(['Misc', 'Pun', 'Programming', 'Spooky'])
        with urllib.request.urlopen(
            f'https://v2.jokeapi.dev/joke/{kategorie}?lang=de&safe-mode',
            context=ctx, timeout=3
        ) as response:
            data = json.loads(response.read().decode())
            if data.get('type') == 'single':
                return data.get('joke')
            elif data.get('type') == 'twopart':
                return data.get('setup') + ' ... ' + data.get('delivery')
    except Exception as e:
        logging.error('get_random_response Fehler: ' + str(e))
    return random.choice(UNNUETZES_WISSEN)
 
app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.DEBUG)
 
VALUEON = ["an","ein","anmachen","einmachen","anschalten","einschalten",]
VALUEOFF = ["aus","ausmachen","ausschalten"]
VALUEUP = ["auf","hoch","hochfahren"]
VALUEDOWN =["zu","runter","ab","runterfahren","heruntefahren","zumachen"]

TYPESSZIMMER = ["esszimmer","esszimmerlicht","große lampe","großes licht","kronleuchter"]
TYPESSZIMMERBALKEN = ["esszimmerbalken","esszimmer balken","esszimmer Balkenlicht","esszimmerbalkenlicht"]
TYPESSZIMMERWAND = ["esszimmer wand","esszimmerwand","esszimmer wandlicht","esszimmerwandlicht"]
TYPBALKONSTECKDOSE = ["balkonsteckdose","balkon Steckdose","steckdose balkon","außensteckdose"]
TYPBALKON = ["balkon","balkonlicht","balkon licht","licht balkon","außenlicht"]
TYPSPEIS = ["speis","speise","abstellkammer","besenkammer","vorratsraum"]
TYPBODENLICHT = ["bodenlicht","bodenspots","bodenlichter","küchenboden"]
TYPKUECHENGANG = ["küchengang","gang","ganglicht"]
TYPKUECHE = ["küche","küchenlicht"]
TYPKUECHNSCHRANK = ["küchenschrank","unterlicht","arbeitsplatte","arbeitsplattenlicht"]
TYPKIND1 = ["kindeins","kind eins","kind 1","kind vorne","büro","bürolicht","lind eins licht"]
TYPKIND2 = ["kindzwei","kind zwei","kind 2","kind hinten","ramschraum","kind zwei licht"]
TYPBADUNTEN = ["bad unten","unteres bad","bad og","kinderbad","gästebad","gästeklo"]
TYPFLURUNTEN = ["flurunten","flur unten","flur og","eingangsflur","flurlicht unten"]
TYPWOHNZIMMER = ["wohnzimmer","wohnzimmerlicht"]
TYPWOHNZIMMERVORNE = ["wohnzimmervorne","wohnzimmer vorne","wohnzimmerlicht vorne"]
TYPWOHNZIMMERWAND = ["wohnzimmerwand","wohnzimmer wand","wohnzimmer wseite","wohnzimmerseite","wohnzimmerwandlicht","wohnzimmer wandlicht"]
TYPANLKEIDE = ["ankleide","kleiderschrank"]
TYPSCHLAFZIMMER = ["schlafzimmer","schlafzimmerlicht"]
TYPSCHLAFZIMMERWAND = ["schlafzimmer wand","schlafzimmerwand","schlafzimmer wandlicht"]
TYPBADOBEN = ["badoben","bad oben","oberesbad","oberes bad","bad dg","elternbad","oberes badlicht","blternbadlicht"]
TYPDUSCHE = ["dusche","badewanne","duschlicht"]
TYPHOBBYRAUM = ["hobbyraum","habyzimmer","Hobbyraumlicht","Babyzimmerlicht"]
TYPHOBBYRAUMNIESCHE = ["hobbyraumniesche","hobbyraum niesche","lagerraum","hobbyraum hinten"]
TYPFLUROBEN = ["fluroben","flur oben","flur dg","flurlicht oben","oberer flur"]
TYPGALERIE = ["galerie","galerielicht"]
TYPBILDLICHT = ["bildlicht"]
TYPFFOBEN = ["fensterfront oben"]
TYPFFLINKS = ["fensterfront links"]
TYPFFRECHTS = ["fensterfront rechts"]
TYPFFMITTE = ["fensterfront mitte"]
TYPFFGES = ["fensterfront","fensterfront komplett","ganze fensterfront","front"]
TYPGES   = ["alles","beide stockwerke"]
TYPGESOBEN = ["oberer stock","alles oben","oben alles","dachgeschoss"]
TYPGESUNTEN = ["unterer stock","alles unten","unten alles","obergeschoss"]

SPECSOFA = ["das sofa","fernsehn","die couch","die kautsch"]
SPECHOCH = ["hoch","schlafen","nach oben","ins bett"]
SPECDUNKEL = ["dunkel","spät","abends","abend","nacht"]
SPECHELL = ["hell","früh","morgens","morgen"]
SPECWEG = ["weg","arbeiten","auf die arbeit","einkaufen","fort"]

 
@ask.launch
def launch():
    speech_text = 'Wilkommen zur Wago Kopplung! Welches Element möchtest du über mich steuern?'
    return question(speech_text).reprompt(speech_text).simple_card(speech_text)
 
@ask.intent('allgemein', mapping = {'value':'Value', 'typ':'Type'})
def doIt(value,typ):
    
    client = connectMod()
    if client == '0':
        return statement('Verbindung fehlgeschlagen')
    
    ret = '0'
    regist = readRegister(client)
    dig = createDig(regist)
    out = createList()

    if value in VALUEON:
        val = 'ein'
        ret = 'ist ein!'
    elif value in VALUEOFF:
        val = 'aus'
        ret = 'ist aus'
    elif value in VALUEUP:
        val = 'auf'
        ret = 'fährt hoch'
    elif value in VALUEDOWN:
        val = 'zu'
        ret = 'fährt zu'
    else:
        ret = '0'
    
    print('Eingabe: ' + typ + ' ' + val)
        
    if typ in TYPESSZIMMER:
        out = handle(dig, ['EsszimmerGross'], val, out)
    elif typ in TYPESSZIMMERBALKEN:
        out = handle(dig, ['EsszimmerBalken'], val, out)
    elif typ in TYPESSZIMMERWAND:
        out = handle(dig, ['EsszimmerWand'], val, out)
    elif typ in TYPBALKONSTECKDOSE:
        out = handle(dig, ['BalkonSteckdose'], val, out)
    elif typ in TYPBALKON:
        out = handle(dig, ['BalkonLicht'], val, out)
    elif typ in TYPSPEIS:
        out = handle(dig, ['Speis'], val, out)
    elif typ in TYPBODENLICHT:
        out = handle(dig, ['KuecheBoden'], val, out)
    elif typ in TYPKUECHENGANG:
        out = handle(dig, ['KuecheGang'], val, out)
    elif typ in TYPKUECHE:
        out = handle(dig, ['Kueche'], val, out)
    elif typ in TYPKUECHNSCHRANK:
        out = handle(dig, ['KuecheSchrank'], val, out)
    elif typ in TYPKIND1:
        out = handle(dig, ['Kind1'], val, out)
    elif typ in TYPKIND2:
        out = handle(dig, ['Kind2'], val, out)
    elif typ in TYPBADUNTEN:
        out = handle(dig, ['BadOG'], val, out)
    elif typ in TYPFLURUNTEN:
        out = handle(dig, ['FlurOG'], val, out)
    elif typ in TYPWOHNZIMMER:
        out = handle(dig, ['Wohnzimmer'], val, out)
    elif typ in TYPWOHNZIMMERVORNE:
        out = handle(dig, ['WohnzimmerVorne'], val, out)
    elif typ in TYPWOHNZIMMERWAND:
        out = handle(dig, ['WohnzimmerWand'], val, out)
    elif typ in TYPANLKEIDE:
        out = handle(dig, ['Ankleide'], val, out)
    elif typ in TYPSCHLAFZIMMER:
        out = handle(dig, ['Schlafzimmer'], val, out)
    elif typ in TYPSCHLAFZIMMERWAND:
        out = handle(dig, ['SchlafzimmerWand'], val, out)
    elif typ in TYPBADOBEN:
        out = handle(dig, ['BadDG'], val, out)
    elif typ in TYPDUSCHE:
        out = handle(dig, ['Dusche'], val, out)
    elif typ in TYPHOBBYRAUM:
        out = handle(dig, ['Hobbyraum'], val, out)
    elif typ in TYPHOBBYRAUMNIESCHE:
        out = handle(dig, ['HobbyraumNiesche'], val, out)
    elif typ in TYPFLUROBEN:
        out = handle(dig, ['FlurOben'], val, out)
    elif typ in TYPGALERIE:
        out = handle(dig, ['Galerie'], val, out)
    elif typ in TYPBILDLICHT:
        out = handle(dig, ['Bildlicht'], val, out)
    elif typ in TYPFFOBEN:
        out = handle(dig, ['FFoben'], val, out)
    elif typ in TYPFFLINKS:
        out = handle(dig, ['FFlinks'], val, out)
    elif typ in TYPFFRECHTS:
        out = handle(dig, ['FFrechts'], val, out)
    elif typ in TYPFFMITTE:
        out = handle(dig, ['FFmitte'], val, out)
    elif typ in TYPFFGES:
        out = fensterfront(dig, val, out)
        ret = "Fensterfront fährt " + val
    elif typ in TYPGES:
        out = alles(dig, val, out)
        ret = "alles " + val
    elif typ in TYPGESUNTEN:
        out = allesUnten(dig, val, out)
        ret = "unterer Stock " + val
    elif typ in TYPGESOBEN:
        out = allesOben(dig, val, out)
        ret = "oberer Stock " + val
    else:
        return statement(typ + ' ' + val + ' nicht gefunden')
    
    write(client,out)
    disconnectMod(client)
    
    return statement(ret)
        
    
    
 
@ask.intent('specialOne', mapping = {'spec':'Spec'})
def doItAgain(spec):
    
    client = connectMod()
    if client == '0':
        return statement('Verbindung fehlgeschlagen')
    
    ret = '0'
    regist = readRegister(client)
    dig = createDig(regist)
    out = createList()
    print('Eingabe: ' + spec)

    if spec in SPECSOFA:
        out = sofa(dig, out)
        ret = 'Macht es euch gemütlich'
    elif spec in SPECHOCH:
        out = hoch(dig, out)
        ret = get_random_response()
    elif spec in SPECDUNKEL:
        out = dunkel(dig, out)
        ret = get_random_response()
    elif spec in SPECHELL:
        out = hell(dig, out)
        ret = 'guten Morgen'
    elif spec in SPECWEG:
        out = weg(dig, out)
        ret = 'bis bald'
    
    ##print(out)
    write(client,out)
    disconnectMod(client)
    
    if (ret != '0'):
        return statement(ret)
    else:
        return statement(typ + ' ' + value + ' nicht gefunden')

@ask.intent('AMAZON.HelpIntent')
def help():
    speech_text = 'You can say hello to me!'
    return question(speech_text).reprompt(speech_text).simple_card('HelloWorld', speech_text)
 
 
@ask.session_ended
def session_ended():
    return "{}", 200
 
if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(host="127.0.0.1", port=5000, debug=False)