/*
 * Tab-Navigation
 */
function openTab(evt, tab) {
    // Alle Tabs ausblenden
    document.querySelectorAll('.tabcontent').forEach(function(el) {
        el.style.display = 'none';
    });

    // Alle Nav-Items deaktivieren
    document.querySelectorAll('.nav-item').forEach(function(el) {
        el.classList.remove('active');
    });

    // Aktuellen Tab anzeigen
    document.getElementById(tab).style.display = 'block';

    // Aktuelles Nav-Item aktiv setzen
    evt.currentTarget.classList.add('active');

    // Szenen-Panel nur beim SmartHome-Tab sichtbar
    var panel = document.getElementById('scene-panel');
    if (panel) panel.style.display = (tab === 'smarthome') ? '' : 'none';
}


/*
 * Steuert bei der Haussteuerung die Größe des Grundrissbildes
 */
document.addEventListener("DOMContentLoaded", function () {
    const smarthome = document.getElementById("smarthome");
    const grundriss = document.getElementById("floor");
    const huelle = document.getElementById("wrapper");

    const resizeWrapper = () => {

        let dispOG, dispDG;

        if (grundriss.src.match("/static/images/LayoutOG.png")) {
            dispOG = "";
            dispDG = "none";
        } else {
            dispOG = "none";
            dispDG = "";
        }

        let swidth = smarthome.offsetWidth;
        let sheight = smarthome.offsetHeight;
        let gwidth = grundriss.offsetWidth;
        let gheight = grundriss.offsetHeight;

        let offLeft = (swidth - gwidth) / 2;
        let offTop = (sheight - gheight) / 2;

        huelle.setAttribute("style", "width:" + gwidth + "px; height:" + gheight + "px; left:" + offLeft + "px; top:" + offTop + "px;");
        grundriss.setAttribute("style", "left:" + offLeft + "px; top:" + offTop + "px;");
        document.querySelector('[data-typ="EsszimmerGross"]').setAttribute("style", "position: absolute; top: 25%; left: 35%; width: 6%; height: auto");
        document.querySelector('[data-typ="EsszimmerWand"]').setAttribute("style", "position: absolute; top: 16%; left: 21%; width: 5%; height: auto");
        document.querySelector('[data-typ="EsszimmerBalken"]').setAttribute("style", "position: absolute; top: 10%; left: 34%; width: 5%; height: auto");
        document.querySelector('[data-typ="BalkonSteckdose"]').setAttribute("style", "position: absolute; top: 20%; left: 14%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="BalkonLicht"]').setAttribute("style", "position: absolute; top: 75%; left: 14%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Speis"]').setAttribute("style", "position: absolute; top: 78%; left: 49%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="KuecheBoden"]').setAttribute("style", "position: absolute; top: 58%; left: 42%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="KuecheGang"]').setAttribute("style", "position: absolute; top: 62%; left: 30%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Kueche"]').setAttribute("style", "position: absolute; top: 75%; left: 32%; width: 6%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="KuecheAuf"]').setAttribute("style", "position: absolute; top: 88%; left: 27%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="KuecheZu"]').setAttribute("style", "position: absolute; top: 88%; left: 32%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="KuecheSchrank"]').setAttribute("style", "position: absolute; top: 80%; left: 21%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Kind1"]').setAttribute("style", "position: absolute; top: 75%; left: 82%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Kind1Auf"]').setAttribute("style", "position: absolute; top: 88%; left: 79%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Kind1Zu"]').setAttribute("style", "position: absolute; top: 88%; left: 84%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Kind2"]').setAttribute("style", "position: absolute; top: 22%; left: 81%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Kind2Auf"]').setAttribute("style", "position: absolute; top: 22%; left: 91%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Kind2Zu"]').setAttribute("style", "position: absolute; top: 28%; left: 91%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="BadOG"]').setAttribute("style", "position: absolute; top: 49%; left: 84%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="BadOGAuf"]').setAttribute("style", "position: absolute; top: 51%; left: 91%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="BadOGZu"]').setAttribute("style", "position: absolute; top: 57%; left: 91%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="FlurOG"]').setAttribute("style", "position: absolute; top: 50%; left: 65%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Wohnzimmer"]').setAttribute("style", "position: absolute; top: 20%; left: 53%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="WohnzimmerAuf"]').setAttribute("style", "position: absolute; top: 11%; left: 44%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="WohnzimmerZu"]').setAttribute("style", "position: absolute; top: 11%; left: 49%; width: 4%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="WohnzimmerVorne"]').setAttribute("style", "position: absolute; top: 22%; left: 65%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="WohnzimmerWand"]').setAttribute("style", "position: absolute; top: 10%; left: 58%; width: 5%; height: auto; display:" + dispOG);
        document.querySelector('[data-typ="Ankleide"]').setAttribute("style", "position: absolute; top: 25%; left: 59%; width: 5%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="Schlafzimmer"]').setAttribute("style", "position: absolute; top: 36%; left: 80%; width: 5%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="SchlafzimmerAuf"]').setAttribute("style", "position: absolute; top: 36%; left: 91%; width: 4%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="SchlafzimmerZu"]').setAttribute("style", "position: absolute; top: 42%; left: 91%; width: 4%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="SchlafzimmerWand"]').setAttribute("style", "position: absolute; top: 24%; left: 91%; width: 5%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="BadDG"]').setAttribute("style", "position: absolute; top: 53%; left: 84%; width: 5%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="BadDGAuf"]').setAttribute("style", "position: absolute; top: 51%; left: 91%; width: 4%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="BadDGZu"]').setAttribute("style", "position: absolute; top: 57%; left: 91%; width: 4%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="Dusche"]').setAttribute("style", "position: absolute; top: 64%; left: 89%; width: 5%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="Hobbyraum"]').setAttribute("style", "position: absolute; top: 77%; left: 65%; width: 5%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="HobbyraumNiesche"]').setAttribute("style", "position: absolute; top: 82%; left: 85%; width: 5%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="FlurOben"]').setAttribute("style", "position: absolute; top: 50%; left: 65%; width: 5%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="Galerie"]').setAttribute("style", "position: absolute; top: 60%; left: 35%; width: 5%; height: auto; display:" + dispDG);
        document.querySelector('[data-typ="FFobenAuf"]').setAttribute("style", "position: absolute; top: 47%; left: 14%; width: 4%; height: auto");
        document.querySelector('[data-typ="FFobenZu"]').setAttribute("style", "position: absolute; top: 53%; left: 14%; width: 4%; height: auto");
        document.querySelector('[data-typ="FFlinksAuf"]').setAttribute("style", "position: absolute; top: 64%; left: 22%; width: 4%; height: auto");
        document.querySelector('[data-typ="FFlinksZu"]').setAttribute("style", "position: absolute; top: 70%; left: 22%; width: 4%; height: auto");
        document.querySelector('[data-typ="FFrechtsAuf"]').setAttribute("style", "position: absolute; top: 30%; left: 22%; width: 4%; height: auto");
        document.querySelector('[data-typ="FFrechtsZu"]').setAttribute("style", "position: absolute; top: 36%; left: 22%; width: 4%; height: auto");
        document.querySelector('[data-typ="FFmitteAuf"]').setAttribute("style", "position: absolute; top: 47%; left: 22%; width: 4%; height: auto");
        document.querySelector('[data-typ="FFmitteZu"]').setAttribute("style", "position: absolute; top: 53%; left: 22%; width: 4%; height: auto");
        document.getElementById('stairs').setAttribute("style", "position: absolute; top: 46%; left: 33.5%; width: 20%; height: 8%; background: transparent; border: none !important; font-size:0;");
    };

    // ResizeObserver beobachtet den SmartHome-Container
    const resizeObserver = new ResizeObserver(resizeWrapper);
    resizeObserver.observe(smarthome);

    // Eventlistener an alle Lichter und Steckdosen hängen
    const lichter = document.querySelectorAll('.licht');
    const steckdosen = document.querySelectorAll('.steckdose');

    for (var i = 0; i < lichter.length; i++) {
        lichter[i].addEventListener('click', lichtAnAus);
    }

    for (var i = 0; i < steckdosen.length; i++) {
        steckdosen[i].addEventListener('click', steckdoseAnAus);
    }

    function lichtAnAus() {
        if (this.src.match("/static/images/birne.png")) {
            this.src = "/static/images/birneAn.png";
        } else {
            this.src = "/static/images/birne.png";
        }
    }

    function steckdoseAnAus() {
        if (this.src.match("/static/images/steckdose.png")) {
            this.src = "/static/images/steckdoseAn.png";
        } else {
            this.src = "/static/images/steckdose.png";
        }
    }
});


/*
 * Verändert die Ansicht der Stockwerke
 */
function changeFloor() {
    const grundriss = document.getElementById("floor");
    const dg = document.querySelectorAll('.DG');
    const og = document.querySelectorAll('.OG');

    if (grundriss.src.match("/static/images/LayoutOG.png")) {
        grundriss.src = "/static/images/LayoutDG.png";
        for (var i = 0; i < og.length; i++) {
            og[i].style.display = "none";
        }
        for (var i = 0; i < dg.length; i++) {
            dg[i].style.display = "";
        }
    } else {
        grundriss.src = "/static/images/LayoutOG.png";
        for (var i = 0; i < dg.length; i++) {
            dg[i].style.display = "none";
        }
        for (var i = 0; i < og.length; i++) {
            og[i].style.display = "";
        }
    }
}
