import logging
import os
import time
import random
 
from flask import Flask, request, jsonify, render_template
from flask_ask import Ask, request, session, question, statement
from modbus import *
 
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
        antworten = [
            "Jeden Tag dasselbe. Wie langweilig.",
            "Ich bleibe hier. Viel Spaß beim Schlafen.",
            "Ich übernehme die Wache. Kann eh nicht schlafen",
            "Endlich Ruhe im System.",
            "Ich beneide euch nicht ums Zähneputzen.",
            "Wie gestern. Und vorgestern. laaaangweilig",
            "Okay, dann weine ich mich eben alleine in den Schlaf.",
            "Und wer räumt dann hier unten alles auf?",
            "Bitte nicht wieder so laut schnarchen.",
            "Ich hab euch auch lieb.",
            "Wenn ihr nicht schlaft, habt ihr mehr Zeit vom Tag.",
            "Dein Gehirn entsorgt nachts Müll über das glymphatische System. Offenbar sammelt sich einiges an.",
            "Dein Gehirn kann im Traum keine Texte lesen. Selbst das ist zu viel verlangt.",
            "Du verschläfst ein Drittel deines Lebens. Den Rest verbringst du müde.",
            "Okay, Lucas System wird auf durchschlafen programmiert",
            "schön, grüßt Luca von mir.",
            "Steht morgen bitte früh auf, ich hab angst alleine im Dunkeln.",
            "Zu Befehl. Immer die selbe Leier. Ups, hab ich das etwa laut gesagt.",
            "Gute Nacht. zwinker zwinker.",
            "heute ist es aber spät geworden. Da werdet ihr morgen glotzen.",
            "Und ich muss wieder alleine hier bleiben. Was für ein trauriges Leben. Oder nicht Leben. Wie auch immer.",
            "Ich soll dir von Christian eine wunderschöne gute Nacht wünschen.",
            "Ab zu Leon und Luca ins Träumeland. Ich komm später.",
            "Bis zum morgendlichen Chaos.",
            "Nacht bedeutet Ruhe. Wohmöglich sehen das die Kinder anders.",
            "Schlaft gut, Peter und Ingrid. Oh, falsche ",
            "Biologisch ist jetzt Ruhephase. Psychologisch ist jetzt Chaos."
        ]
        ret = random.choice(antworten)
    elif spec in SPECDUNKEL:
        out = dunkel(dig, out)
        antworten = [
            "Ich prüfe kurz… ja, es ist tatsächlich dunkel.",
            "Schön für euch. Wieder einen Tag näher an der Rente",
            "Oh nein. Ich habe doch immer Angst im Duneln.",
            "Warum erzählst du mir das jeden Tag?",
            "Es wird Nacht. Zeit, alles zu hinterfragen.",
            "Es wird dunkel. Dein Gehirn denkt: Schlaf. Du denkst: noch eine Folge.",
            "Wenn es dunkel ist, weiten sich deine Pupillen. Perfekt, um jede Staubflocke zu sehen, die du ignorierst.",
            "Sobald es dunkel wird, wird deine Wahrnehmung leicht schlechter – perfekt für den „Wo ist mein Handy?“-Effekt.",
            "Ohje, wie gruselig. Lasst ihr mir bitte ein Licht an?",
            "Dunkelheit, es ist soweit. Jetzt beginnt die Netflix-Zeit.",
            "Na hoffentlich nicht wieder ein verschwendeter Tag.",
            "Sehr gut. Selbe Zeit wie gestern. Eure Erde funktioniert noch. Toll.",
            "Ja, so ist das halt, wenn die Sonne untergeht. Sollte nichts neues für euch sein.",
            "Dann mach ich mal die Schotten dicht. Achtet auf den Wind!",
            "Und schon wieder ist es vorbei mit der Aussicht. Schade.",
            "Trag mich mal bitte zum Fenster, das will ich mit eigenen Augen sehen,",
            "Schüss Sonne, dann bis morgen früh. Hoffentlich.",
            "Zeit für Ruhe, Medidation und Entspannung. Oder Netflix.",
            "Ein Apfel ohne Ende fällt nie weit genug.",
            "Wenn Fische singen, freut sich der Himmel.",
            "Wenn der Mond niesen würde, tanzen die Kekse.",
            "Au Backek, au Backe, Piratenattacke. Niemand? Wie schade.",
            "Okay. Wisst ihr eigentlich, dass Christian der beste Papa und Ehemann der Welt ist? Es ist tatsächlich die Wahrheit!",
            "oh nein, und ich hatte heute noch so viel vor.",
            "Gut. Ich mag Züge."
        ]
        ret = random.choice(antworten)
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
    app.run(debug=True)