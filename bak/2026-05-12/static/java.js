/*
 * Alle Informationen zur Navbar
 */

var Nav = (function () {
    var nav = $(".nav"),
        burger = $(".burger"),
        page = $(".page"),
        section = $(".section"),
        link = nav.find(".nav__link"),
        navH = nav.innerHeight(),
        isOpen = true,
        hasT = false;

    var toggleNav = function () {
        nav.toggleClass("nav--active");
        burger.toggleClass("burger--close");
        shiftPage();
    };

    var shiftPage = function () {
        if (!isOpen) {
            page.css({
                transform: "translateY(" + navH + "px)",
                "-webkit-transform": "translateY(" + navH + "px)"
            });
            isOpen = true;
        } else {
            page.css({
                transform: "none",
                "-webkit-transform": "none"
            });
            isOpen = false;
        }
    };

    var switchPage = function (e) {
        var self = $(this);
        var i = self.parents(".nav__item").index();
        var s = section.eq(i);
        var a = $("section.section--active");
        var t = $(e.target);

        if (!hasT) {
            if (i == a.index()) {
                return false;
            }
            a.addClass("section--hidden").removeClass("section--active");

            s.addClass("section--active");

            hasT = true;

            a.on("transitionend webkitTransitionend", function () {
                $(this).removeClass("section--hidden");
                hasT = false;
                a.off("transitionend webkitTransitionend");
            });
        }

        return false;
    };

    var keyNav = function (e) {
        var a = $("section.section--active");
        var aNext = a.next();
        var aPrev = a.prev();
        var i = a.index();

        if (!hasT) {
            if (e.keyCode === 37) {
                if (aPrev.length === 0) {
                    aPrev = section.last();
                }

                hasT = true;

                aPrev.addClass("section--active");
                a.addClass("section--hidden").removeClass("section--active");

                a.on("transitionend webkitTransitionend", function () {
                    a.removeClass("section--hidden");
                    hasT = false;
                    a.off("transitionend webkitTransitionend");
                });
            } else if (e.keyCode === 39) {
                if (aNext.length === 0) {
                    aNext = section.eq(0);
                }

                aNext.addClass("section--active");
                a.addClass("section--hidden").removeClass("section--active");

                hasT = true;

                aNext.on("transitionend webkitTransitionend", function () {
                    a.removeClass("section--hidden");
                    hasT = false;
                    aNext.off("transitionend webkitTransitionend");
                });
            } else {
                return;
            }
        }
    };

    var bindActions = function () {
        burger.on("click", toggleNav);
        link.on("click", switchPage);
        $(document).on("ready", function () {
            page.css({
                transform: "translateY(" + navH + "px)",
                "-webkit-transform": "translateY(" + navH + "px)"
            });
        });
        $("body").on("keydown", keyNav);
    };

    var init = function () {
        bindActions();
    };

    return {
        init: init
    };
})();

Nav.init();

/*
 * Tabs öffnen und ausblenden
 */

function openTab(evt, tab) {
    // Declare all variables
    var i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(tab).style.display = "block";
    evt.currentTarget.className += " active";
}


/*
 * steuer bei der Haussteuerung die größe des GrundrissBildes 
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
    }

    // Erstellen eines ResizeObserver-Objekts
    const resizeObserver = new ResizeObserver(resizeWrapper);

    // Hinzufügen des Elements zum Beobachten durch den ResizeObserver
    resizeObserver.observe(smarthome);


    // Eventlistener an alle Lichter hängen, wo geklickt werden kann

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
            og[i].style.display = "none"
        }
        for (var i = 0; i < dg.length; i++) {
            dg[i].style.display = ""
        }
    } else {
        grundriss.src = "/static/images/LayoutOG.png";
        for (var i = 0; i < dg.length; i++) {
            dg[i].style.display = "none"
        }
        for (var i = 0; i < og.length; i++) {
            og[i].style.display = ""
        }
    }

}