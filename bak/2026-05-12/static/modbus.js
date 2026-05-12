const eles = ['BadDG' //12336
    , 'Dusche' //12337
    , 'SchlafzimmerWand' //12338
    , 'Schlafzimmer' //12339
    , 'Ankleide' //12340
    , 'Bildlicht' //12341
    , 'FlurOben' //12342
    , 'EsszimmerGross' //12343
    , 'Galerie' //12344
    , 'Hobbyraum' //12345
    , 'HobbyraumNiesche' //12346
    , '' //12347
    , '' //12348
    , '' //12349
    , 'FlurOG' //12350
    , '' //12351
    , 'KuecheSchrank' //12352
    , 'Kueche' //12353
    , 'Speis' //12354
    , 'KuecheGang' //12355
    , '' //12356 (*??*)
    , 'KuecheBoden' //12357
    , 'Kind1' //12358
    , 'BadOG' //12359
    , 'Kind2' //12360
    , 'Wohnzimmer' //12361
    , 'WohnzimmerWand' //12362
    , 'WohnzimmerVorne' //12363
    , 'EsszimmerBalken' //12364
    , '' //12365
    , 'EsszimmerWand' //12366
    , '' //12367
    , 'BalkonSteckdose' //12368
    , 'BalkonLicht' //12369
    , '' //12370
      ]


$(function () {
    $(".cbutton").click(function (event) {
        let type = $(this).data("typ");
        type = type.replace("Auf", "")
        type = type.replace("Zu","")
        let valu = $(this).data("val");
        $.getJSON($SCRIPT_ROOT + '/Modbus', { typ: type, val: valu },
            function (data) { });
        return false;
    });
});

$(document).ready(function () {
    function create() {
        $.getJSON($SCRIPT_ROOT + '/Read', {},
            function (data) {
                dat = data.result;
            });
    }

    function updateOrders() {
        let element;
        $.getJSON($SCRIPT_ROOT + '/Read', {},
            function (data) {
                var statusNeu = data.result;
                let string = "";
                for (let i = 0; i < statusNeu.length; i++) {

                    if (eles[i] !== "") {

                        element = document.querySelector('[data-typ="' + eles[i] + '"]');
                        if (element) {

                            if (statusNeu[i] && element.src.match("/static/images/steckdose.png")) {
                                element.src = "/static/images/steckdoseAn.png"
                            }
                            if (statusNeu[i] && element.src.match("/static/images/birne.png")) {
                                element.src = "/static/images/birneAn.png"
                            }
                            if (!statusNeu[i] && element.src.match("/static/images/steckdoseAn.png")) {
                                element.src = "/static/images/steckdose.png"
                            }
                            if (!statusNeu[i] && element.src.match("/static/images/birneAn.png")) {
                                element.src = "/static/images/birne.png"
                            }
                        }
                    }
                }
                setTimeout(updateOrders, 2000);
            });
    }
    updateOrders();
});