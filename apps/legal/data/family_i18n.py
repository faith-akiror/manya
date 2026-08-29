"""Database translations for Family (Luganda, Ateso, Acholi).

These strings are general-information translations for USSD/SMS/API.
They are stored as ContentTranslation rows (manual, reviewed) so the
central TranslationService can serve them without hardcoded language
branches. Administrators should still review them.
"""

FAMILY_CATEGORY_I18N = {
    "lg": {
        "name": "Amaka",
        "description": "Amateeka agakwata ku bufumbo, abaana, obutabanguko mu maka n'obusika.",
    },
    "teo": {
        "name": "Auren",
        "description": "Eitunganan lo eongat, ikoku, ajokot ka inheritance.",
    },
    "ach": {
        "name": "Gang",
        "description": "Cik ma mako nyom, litino, tim gero i gang kede oneo.",
    },
}

# Shared next-step block used where a topic does not need a unique action list.
HELP_I18N = {
    "lg": (
        "1. Wandiika ekyabaawo era kung'aanye ebiwandiiko. "
        "2. Tuukirira omukozi wa probation, poliisi ey'amaka n'abaana, oba FIDA. "
        "3. Weebuuze ku muteesa w'amateeka ku nsonga yo."
    ),
    "teo": (
        "1. Ngot elosio ka documents. "
        "2. Kibo probation officer, police lo family, kosi FIDA. "
        "3. Kibo legal aid lo eongat kon."
    ),
    "ach": (
        "1. Coo gin ma otime ki coko waraga. "
        "2. Citi bot probation, police me gang ki litino, onyo FIDA. "
        "3. Peny lakwena me cik pi lokki."
    ),
}

DOCS_I18N = {
    "lg": "Ebiwandiiko eby'obufumbo oba abaana, endagaano, obujulizi obuliwo.",
    "teo": "Documents lo eongat, ikoku, kosi land.",
    "ach": "Waraga me nyom, litino, onyo ngom.",
}


def _pack(name, summary, rights, means=None, next_steps=None, docs=None, title=None):
    return {
        "name": name,
        "title": title or name,
        "summary": summary,
        "rights_information": rights,
        "what_this_means": means or summary,
        "next_steps": next_steps,
        "documents_required": docs,
    }


def _all_langs(lg, teo, ach):
    return {"lg": lg, "teo": teo, "ach": ach}


FAMILY_TOPIC_I18N = {
    "family-marriage-recognition": _all_langs(
        _pack(
            "Obufumbo n'okumanyibwa mu mateeka",
            "Amateeka ga Uganda gamanyisa ebitundu eby'obufumbo eby'enjawulo. Obufumbo bumanyibwa nga bwe buyitiddwa mu ntegeka za civil, customary oba eby'eddiini.",
            "Ettwale lya 31 erya Constitution liwa abasajja n'abakazi ab'emyaka 18 obuyinza okufumbiriganwa era nti balina eddembe lye kimu mu bufumbo.",
        ),
        _pack(
            "Eongat ka nginar lo cik",
            "Cik lo Uganda kimanyi etunganan eongat. Eongat ejeni kane etunganan lo civil, customary kosi dini.",
            "Constitution Article 31 ebeonokin ikiliok ka beru lo mwaka 18 aingarakin eongat ka edioos lo ebeu.",
        ),
        _pack(
            "Nyom ki ngec i cik",
            "Cik me Uganda ngeyo kit nyom mapol. Nyom ngeye ka kitye kit ma cik mito.",
            "Article 31 me Constitution miyo twero bot coo ki mon ma mwaka 18 me nyom ki twero marom i nyom.",
        ),
    ),
    "family-types-of-marriage": _all_langs(
        _pack(
            "Enkola z'obufumbo",
            "Waliwo obufumbo bwa civil, customary n'obw'eddiini nga amateeka gabikkulira.",
            "Enkola y'obufumbo ey'enjawulo erina amateeka ag'enjawulo. Polygamy tewali mu ngeri yee mu ntegeka zonna.",
        ),
        _pack(
            "Adioos lo eongat",
            "Eongat lo civil, customary ka dini ejeni kane cik ebeonokin.",
            "Adioos lo eongat ebeonokin nginar ka polygamy pe etunganan lo civil.",
        ),
        _pack(
            "Kit nyom",
            "Tye nyom me registrar, nyom me kwer, ki nyom me dini.",
            "Kit nyom ma iketo nongo twero ki tic ma cik mito.",
        ),
    ),
    "family-marriage-registration": _all_langs(
        _pack(
            "Okwewandiisa obufumbo",
            "Okwewandiisa kuleeta ekiwandiiko eky'obufumbo. Obufumbo bwa customary burina entegeka y'okwewandiisa.",
            "Ekiwandiiko kiyamba okukakasa obufumbo eri abaana, ettaka n'obusika.",
        ),
        _pack(
            "Registration lo eongat",
            "Registration ebeonokin document lo eongat. Customary marriage kewoto registration.",
            "Document ebeonokin nginar lo ikoku ka inheritance.",
        ),
        _pack(
            "Coo nyom",
            "Coo nyom keto waraga me cik. Nyom me kwer bene twero cooye.",
            "Waraga konyo me ngeyo nyom pi litino, ngom ki oneo.",
        ),
    ),
    "family-marriage-requirements": _all_langs(
        _pack(
            "Ebyetaagisa mu bufumbo",
            "Constitution eteeka emyaka 18 ng'emyaka egy'okufumbiriganwa. Ebirala byesigamizibwa ku ngeri y'obufumbo.",
            "Omuntu ali mu bufumbo obumu teyinza kufumbirwa omulala mu ngeri y'obumu.",
        ),
        _pack(
            "Ebeonokin lo eongat",
            "Constitution ebeonokin mwaka 18. Ebeonokin lo adioos lo eongat ejeni.",
            "Ikiliok lo eongat lo monogamous pe kewoto eongat naitet.",
        ),
        _pack(
            "Gin ma nyom mito",
            "Constitution tero mwaka 18. Jami mukene lubo kit nyom.",
            "Ngat ma tye i nyom acel pe twero keto nyom mukene ka nyom pud tye.",
        ),
    ),
    "family-spouse-rights": _all_langs(
        _pack(
            "Eddembe n'obuvunaanyizibwa bw'abafumbo",
            "Abafumbo balina eddembe lye kimu mu bufumbo. Balina n'obuvunaanyizibwa eri abaana.",
            "Article 31 erya Constitution lyogera ku ddembe lye kimu mu bufumbo, mu kufumbiriganwa n'okuvaamu.",
        ),
        _pack(
            "Ebeonokin lo eongat ka ikoku",
            "Eongat ebeonokin edioos lo ebeu. Ikoku kewoto care.",
            "Constitution Article 31 ebeonokin ebeu lo eongat.",
        ),
        _pack(
            "Twero ki tic pa monyom",
            "Monyom tye ki twero marom. Gin bene tye ki tic bot litino.",
            "Article 31 tero twero marom i nyom, i kare me nyom ki ka nyom otum.",
        ),
    ),
    "family-customary-marriage": _all_langs(
        _pack(
            "Obufumbo bw'ennono",
            "Obufumbo bw'ennono buyitibwa mu mpisa z'ekika. Waliwo amateeka ag'okwewandiisa.",
            "Okwewandiisa kuyamba okukakasa obufumbo. Polygamy eyinza okubeerawo mu nnono ezimu.",
        ),
        _pack(
            "Eongat lo kwer",
            "Eongat lo kwer ejeni kane adioos lo auren. Registration ebeonokin.",
            "Registration ebeonokin nginar. Polygamy kewoto kane kwer ebeonokin.",
        ),
        _pack(
            "Nyom me kwer",
            "Nyom me kwer kitye kit pa kaka. Cik miyo yo me cooye.",
            "Coo nyom konyo me ngeyo. Polygamy twero tye i kwer mogo.",
        ),
    ),
    "family-civil-marriage": _all_langs(
        _pack(
            "Obufumbo bwa registrar",
            "Obufumbo bwa civil buyitibwa mu maaso ga registrar. Buli bumu (monogamous).",
            "Terekeeta ekiwandiiko ky'obufumbo. Toyinza kufumbirwa omulala ng'obufumbo buno bukyaliwo.",
        ),
        _pack(
            "Eongat lo registrar",
            "Eongat lo civil kewoto registrar. Monogamous.",
            "Ngot certificate. Pe kewoto eongat naitet kane eongat lo civil ejeni.",
        ),
        _pack(
            "Nyom me registrar",
            "Nyom me cik kitye i nyim registrar. Nyom acel.",
            "Gwok waraga. Pe iket nyom mukene ka nyom man pud tye.",
        ),
    ),
    "family-religious-marriage": _all_langs(
        _pack(
            "Obufumbo bw'eddiini",
            "Obufumbo obumu obw'eddiini bumanyibwa nga bwe buyitiddwa mu mateeka agakwata ku ddiini eyo.",
            "Omukisa gwokka mu kkanisa oba mu mizikiti guyinza obutaba bufumbo mu mateeka. Weebuuze.",
        ),
        _pack(
            "Eongat lo dini",
            "Eongat lo dini ejeni kane cik lo Uganda ebeonokin.",
            "Blessing lo kanisa kosi mosque pe kere eongat. Kibo legal aid.",
        ),
        _pack(
            "Nyom me dini",
            "Nyom me dini ngeye ka cik me Uganda ye ngeyo.",
            "Gwedo i kanisa kene romo pe bedo nyom i cik. Peny lakwena.",
        ),
    ),
    "family-polygamous-marriage": _all_langs(
        _pack(
            "Obufumbo obw'abakyala abangi",
            "Okufumbirwa abakyala abangi kuyinza okubeerawo mu bufumbo bw'ennono. Obufumbo bwa civil tebukkiriza.",
            "Okufumbirwa omulala ng'oli mu bufumbo obumu kiyinza okuleeta ensonga z'amateeka.",
        ),
        _pack(
            "Eongat lo beru kane kane",
            "Polygamy kewoto customary kane kwer ebeonokin. Civil pe.",
            "Eongat naitet kane civil ejeni ebeonokin ajokot lo cik.",
        ),
        _pack(
            "Nyom me mon mapol",
            "Nyom me mon mapol twero tye i kwer. Nyom me registrar pe ye ye.",
            "Keto mon mukene ka tye i nyom acel romo kelo peko me cik.",
        ),
    ),
    "family-invalid-marriage": _all_langs(
        _pack(
            "Obufumbo obutali butuufu",
            "Omukolo guyinza obutaba bufumbo singa emyaka, okukkiriza oba obufumbo obulala bwe buzibu.",
            "Kkooti ye esalawo ensonga z'obufumbo. Toyinza kwesalira ggwe.",
        ),
        _pack(
            "Eongat pe etunganan",
            "Eongat pe etunganan kane mwaka, consent kosi eongat naitet ejeni.",
            "Court ebeonokin nginar. Pe kibo decision kon kere.",
        ),
        _pack(
            "Nyom ma pe tye kakare",
            "Nyom romo pe bedo nyom ka mwaka, ye ye, onyo nyom mukene pud tye.",
            "Court aye ngoo. Pe inong keni.",
        ),
    ),
    "family-divorce": _all_langs(
        _pack(
            "Okuggya obufumbo",
            "Okuggya obufumbo kuba kusala kwa kkooti, si kwawukana kwokka.",
            "Kkooti eggya obufumbo ku nsonga amateeka ge gawa. Abaana n'ettaka biteekebwako.",
        ),
        _pack(
            "Ajokot lo eongat",
            "Divorce ebeonokin court, pe aicikokin kere.",
            "Court ebeonokin grounds lo cik. Ikoku ka land kewoto.",
        ),
        _pack(
            "Keto nyom woko",
            "Keto nyom woko tye tic pa court, pe poko gang kene.",
            "Court keto nyom woko pi tpeng ma cik ye. Litino ki ngom bene kibi.",
        ),
    ),
    "family-legal-separation": _all_langs(
        _pack(
            "Okwewulira mu mateeka",
            "Abafumbo bayinza okubeera abeenkanawo nga tebaggye bufumbo. Kkooti eyinza okusalawo ku baana n'obuyambi.",
            "Okwewulira tekumalawo bufumbo. Obuyambi bw'abaana buyinza okusabibwa.",
        ),
        _pack(
            "Aicikokin lo cik",
            "Eongat kewoto aicikokin pe divorce. Court kewoto ikoku ka maintenance.",
            "Aicikokin pe ebeonokin eongat etum. Ikoku kewoto support.",
        ),
        _pack(
            "Poko i cik",
            "Monyom twero bedo cen ka pe giketo nyom woko. Court twero ciko litino.",
            "Poko pe tyeko nyom. Kony pa litino pud twero penye.",
        ),
    ),
    "family-grounds-for-divorce": _all_langs(
        _pack(
            "Ensonga z'okuggya obufumbo",
            "Kkooti tevaamu bufumbo lwa butasobagana kwokka. Waliwo ensonga amateeka ge gawa.",
            "Ensonga ziyinza okuba adultery, cruelty oba desertion nga amateeka bwe gatyo. Kale kale weebuuze.",
        ),
        _pack(
            "Grounds lo divorce",
            "Court pe ebeonokin divorce kane aicikokin kere. Cik ebeonokin grounds.",
            "Adultery, cruelty kosi desertion kewoto. Kibo legal aid.",
        ),
        _pack(
            "Tpeng me keto nyom woko",
            "Court pe keto nyom woko pi cimo kene. Cik tero tpeng.",
            "Adultery, tim gero onyo weko gang romo tye. Peny lakwena.",
        ),
    ),
    "family-divorce-procedure": _all_langs(
        _pack(
            "Entegeka y'okuggya obufumbo",
            "Okuggya obufumbo kutandikira mu kkooti n'okuwereza omukyala oba omusajja omulala.",
            "Funa ffoomu ezituufu okuva mu registry oba mu legal aid, so si 'okuggya mangu' okw'obulimba.",
        ),
        _pack(
            "Procedure lo divorce",
            "Divorce kewoto petition lo court ka service.",
            "Kibo forms lo registry kosi legal aid. Pe kibo quick divorce lo ajokot.",
        ),
        _pack(
            "Yo me keto nyom woko",
            "Cak i court ki cwal waraga bot monyom mukene.",
            "Nong form ki registry onyo legal aid. Pe wil nyom maber maber.",
        ),
    ),
    "family-children-during-divorce": _all_langs(
        _pack(
            "Abaana mu kuggya obufumbo",
            "Abaana be beesigamizibwa ku magoba gaabwe, si ku busungu bw'abazadde.",
            "Children Act eteeka welfare w'omwana okuba ekisooka. Toyinza kukwasa mwana ng'okozesa.",
        ),
        _pack(
            "Ikoku lo divorce",
            "Ikoku kewoto welfare, pe anger lo eongat.",
            "Children Act ebeonokin welfare. Pe kibo ikoku lo bargain.",
        ),
        _pack(
            "Litino i kare me keto nyom woko",
            "Ber pa latin aye mukene, pe kiniga pa anyera.",
            "Children Act tero ber pa latin. Pe igeng latin pi laro.",
        ),
    ),
    "family-maintenance-after-divorce": _all_langs(
        _pack(
            "Obuyambi oluvannyuma lw'okuggya obufumbo",
            "Omwana oba omufumbo ayinza okusaba obuyambi mu ssente. Kkooti esalawo.",
            "Obuyambi bw'abaana buyinza okusabibwa mu kkooti. Tokkiriza kwekiriza kwokka.",
        ),
        _pack(
            "Maintenance lo divorce",
            "Ikoku kosi eongat kewoto maintenance. Court ebeonokin.",
            "Kibo court kosi probation kane support pe ejeni.",
        ),
        _pack(
            "Kony lacen me keto nyom woko",
            "Latin onyo monyom twero penyo kony me cente. Court ngoo.",
            "Ka kony pe, cit i court onyo bot probation.",
        ),
    ),
    "family-child-rights": _all_langs(
        _pack(
            "Eddembe ly'abaana",
            "Buli mwana alina eddembe ery'obulamu, ebyenjigiriza, obulamu obulungi n'okukuumibwa.",
            "Article 34 n'amateeka g'abaana gakuuma abaana. Mwana ye ali wansi w'emyaka 18.",
        ),
        _pack(
            "Ebeonokin lo ikoku",
            "Ikoku ebeonokin life, education, health ka protection.",
            "Article 34 ka Children Act ebeonokin. Ikoku lo mwaka pe 18.",
        ),
        _pack(
            "Twero pa litino",
            "Latin ki twero me kwo, kwan, yot kom ki gwoko.",
            "Article 34 ki Children Act gwoko litino. Latin aye ngat ma mwaka pe odek.",
        ),
    ),
    "family-parental-responsibility": _all_langs(
        _pack(
            "Obuvunaanyizibwa bw'abazadde",
            "Abazadde balina okuyisa omwana: emmere, ekyalo, ebyenjigiriza n'obujjanjabi.",
            "Obuvunaanyizibwa si bwa oyo yennyini omwana gw'abeera naye. Omwana asobola okusaba obuyambi.",
        ),
        _pack(
            "Ebeonokin lo eongat lo ikoku",
            "Eongat kewoto food, school, health ka protection lo ikoku.",
            "Responsibility pe lo eongat lo ikoku kere. Maintenance kewoto.",
        ),
        _pack(
            "Tic pa anyera",
            "Anyera myero gimi cam, ot, kwan ki yat bot latin.",
            "Tic pe pa ngat ma latin bedo bote kene. Kony me cente twero penye.",
        ),
    ),
    "family-child-custody": _all_langs(
        _pack(
            "Okukuuma omwana",
            "Okukuuma kwe kuba n'omwana n'okusalawo ku bulamu bwe. Kkooti esalawo ku magoba g'omwana.",
            "Tewali ntegeka nti omwana 'wa kitaawe' oba 'wa nnyina' yokka. Welfare ye esooka.",
        ),
        _pack(
            "Custody lo ikoku",
            "Custody ebeonokin nginar lo ikoku ka decision. Court ebeonokin welfare.",
            "Pe cik lo papa kosi mama kere. Welfare lo ikoku ebeonokin.",
        ),
        _pack(
            "Gwoko latin",
            "Gwoko aye ngat ma latin bedo bote. Court neno ber pa latin.",
            "Pe tye cik ni latin pa won onyo pa min kene. Ber pa latin aye mukene.",
        ),
    ),
    "family-child-access": _all_langs(
        _pack(
            "Okulaba omwana",
            "Omuzadde atabeera n'omwana ayinza okumulaba, okugyako nga waliwo akatyabaga.",
            "Kkooti eyinza okuteeka entegeka z'okulaba. Tokozesa buyinza.",
        ),
        _pack(
            "Access lo ikoku",
            "Eongat pe lo ikoku kewoto access kane safety ejeni.",
            "Court kewoto timetable. Pe kibo force.",
        ),
        _pack(
            "Neno latin",
            "Ngat ma pe bedo ki latin twero nene ka pe tye lworo.",
            "Court twero ciko neno. Pe tii ki tek.",
        ),
    ),
    "family-child-maintenance": _all_langs(
        _pack(
            "Obuyambi eri omwana",
            "Abazadde balina okuyisa omwana: emmere, ebyambalo, ebyenjigiriza n'obujjanjabi, newakubadde nga tebafumbiriganwa.",
            "Children Act ekkiriza okusaba obuyambi mu kkooti. Ssente z'omwana, si kugoba muzadde.",
            next_steps=(
                "1. Kung'aanya ekiwandiiko eky'obulango n'ebisaaso. "
                "2. Saba obuyambi mu kkooti y'amaka n'abaana oba ew'omukozi wa probation. "
                "3. Weebuuze ku FIDA oba legal aid."
            ),
        ),
        _pack(
            "Maintenance lo ikoku",
            "Eongat kewoto food, clothing, school ka health lo ikoku, kane pe eongat.",
            "Children Act kewoto application lo court. Ssente lo ikoku, pe punishment.",
            next_steps=(
                "1. Ngot birth record ka bills. "
                "2. Kibo family court kosi probation. "
                "3. Kibo FIDA kosi legal aid."
            ),
        ),
        _pack(
            "Kony pa latin",
            "Anyera tye ki tic me miyo cam, bongo, kwan ki yat bot latin, kadi pe gunyome.",
            "Children Act ye yo me penyo kony i court. Cente pa latin, pe kum.",
            next_steps=(
                "1. Cok waraga me nywal ki bill. "
                "2. Penyo i court me gang ki litino onyo bot probation. "
                "3. Cit bot FIDA onyo legal aid."
            ),
        ),
    ),
    "family-child-protection": _all_langs(
        _pack(
            "Okukuumibwa kw'abaana",
            "Amateeka gakuuma abaana okuva mu nkelekele, okulekerera n'okukozesebwa.",
            "Buli omu ayinza okutegeeza probation oba poliisi omwana ali mu kabi.",
        ),
        _pack(
            "Protection lo ikoku",
            "Cik ebeonokin ikoku lo abuse ka neglect.",
            "Kibo probation kosi police kane ikoku ejeni lo danger.",
        ),
        _pack(
            "Gwoko litino",
            "Cik gwoko litino ki tim gero, weko ki tic marac.",
            "Ngat mo twero tito bot probation onyo police ka latin tye i lworo.",
        ),
    ),
    "family-child-abuse": _all_langs(
        _pack(
            "Okuyisa omwana obubi",
            "Okukuba, okukozesa mu kwegatta, n'okuyisa mu mmeeme kuba nkelekele.",
            "Tegeeza poliisi ey'amaka n'abaana. Omwana ayinza okwetaaga obujjanjabi n'ekifo eky'obutebenkevu.",
        ),
        _pack(
            "Abuse lo ikoku",
            "Physical, sexual ka emotional abuse ebeonokin ajokot.",
            "Kibo police lo family. Ikoku kewoto health ka safety.",
        ),
        _pack(
            "Tim gero bot latin",
            "Goyo, tim me cop, ki tim me cwiny aye tim gero.",
            "Tito bot police me gang ki litino. Latin myero nong yat ki kabedo maber.",
        ),
    ),
    "family-child-neglect": _all_langs(
        _pack(
            "Okulekerera omwana",
            "Okulekerera kwe kuba nga omwana tawaabwa ebyetaago. Kiyinza okutegeezebwa.",
            "Tegeeza probation. Enkola y'okukuuma ey'amateeka esinga okutwala omwana mu ngeri etali ntuufu.",
        ),
        _pack(
            "Neglect lo ikoku",
            "Neglect ebeonokin kane food, school kosi care pe ejeni.",
            "Kibo probation. Pe kibo ikoku lo force.",
        ),
        _pack(
            "Weko latin",
            "Weko aye ka latin pe nongo cam, kwan onyo gwoko.",
            "Tito bot probation. Pe kwany latin ki tek.",
        ),
    ),
    "family-child-abduction": _all_langs(
        _pack(
            "Okuloga omwana",
            "Okutwala omwana ng'oyita mu mateeka kiba kizibu kinene, naddala okumugenda naye ebweru.",
            "Tuukirira poliisi amangu. Terekeeta ebiwandiiko by'obulango.",
        ),
        _pack(
            "Abduction lo ikoku",
            "Kibo ikoku pe lo cik ebeonokin ajokot, kane border kewoto.",
            "Kibo police amangu. Ngot birth record ka custody order.",
        ),
        _pack(
            "Kwanyo latin",
            "Kwanyo latin ma pe tye i cik tye peko madit, dong ka kela loka.",
            "Citi bot police oyot. Gwok waraga me nywal.",
        ),
    ),
    "family-children-outside-marriage": _all_langs(
        _pack(
            "Abaana abazaalibwa nga tebafumbiriddwa",
            "Omwana alina eddembe ly'okuyisibwa n'obuyambi newakubadde abazadde tebafumbiriganwa.",
            "Wandiisa obulango. Osaba obuyambi singa omuzadde agaana.",
        ),
        _pack(
            "Ikoku pe lo eongat",
            "Ikoku ebeonokin care ka maintenance kane pe eongat.",
            "Registration lo birth. Maintenance kewoto kane support pe.",
        ),
        _pack(
            "Litino ma kinywal ma pe gunyome",
            "Latin tye ki twero me gwoko ki kony kadi anyera pe gunyome.",
            "Coo nywal. Penyo kony ka ngat mo pe miyo.",
        ),
    ),
    "family-paternity": _all_langs(
        _pack(
            "Obuzadde bw'omusajja",
            "Okumanya kitaawe w'omwana kikwata ku buyambi, erinnya n'obusika.",
            "Kkooti eyinza okusalawo, nga mw'otwalidde okukebera kwa DNA nga kkooti bwe ekiragira.",
        ),
        _pack(
            "Paternity",
            "Paternity ebeonokin maintenance, name ka inheritance.",
            "Court kewoto nginar. DNA kewoto kane court ebeonokin.",
        ),
        _pack(
            "Ngeyo won latin",
            "Ngeyo won latin keto kony, nying ki oneo.",
            "Court twero ngoo. DNA tye ka court ye ciko.",
        ),
    ),
    "family-birth-registration": _all_langs(
        _pack(
            "Okwewandiisa obulango",
            "Buli mwana alina okwewandiisa. Kiyamba ku ssomero, obulamu n'obusika.",
            "Genda ewa NIRA oba weebuuze ew'omukozi wa probation. Togula ndagaano z'obulimba.",
        ),
        _pack(
            "Registration lo birth",
            "Ikoku kewoto registration. School, health ka inheritance kewoto.",
            "Kibo NIRA kosi probation. Pe kibo certificate lo ajokot.",
        ),
        _pack(
            "Coo nywal",
            "Latin myero cooye. Konyo kwan, yot kom ki oneo.",
            "Cit bot NIRA onyo probation. Pe wil waraga me bwola.",
        ),
    ),
    "family-domestic-violence": _all_langs(
        _pack(
            "Obutabanguko mu maka",
            "Obutabanguko mulimu okukuba, okukozesa mu kwegatta, okuyisa mu mmeeme n'okuziyiza ssente. Amateeka tegekkiriza.",
            "Domestic Violence Act, 2010 ewa protection orders. Genda mu kifo eky'obutebenkevu era tegeeza poliisi.",
        ),
        _pack(
            "Ajokot lo auren",
            "Physical, sexual, emotional ka economic abuse ebeonokin domestic violence.",
            "Domestic Violence Act 2010 kewoto protection order. Kibo police ka safety.",
        ),
        _pack(
            "Tim gero i gang",
            "Goyo, tim me cop, tim me cwiny ki gengo cente aye tim gero i gang.",
            "Domestic Violence Act 2010 miyo protection order. Cit i kabedo maber ki tito bot police.",
        ),
    ),
    "family-reporting-domestic-violence": _all_langs(
        _pack(
            "Okutegeeza obutabanguko mu maka",
            "Osobola okutegeeza poliisi oba LC. Toyetaaga lukusa lwa eyakuyisa.",
            "Saba basse ekirango. Terekeeta namba. Legal aid eyinza okukugenda naawe.",
        ),
        _pack(
            "Report lo ajokot lo auren",
            "Kibo police kosi LC. Consent lo abuser pe ebeonokin.",
            "Ngot complaint number. Legal aid kewoto.",
        ),
        _pack(
            "Tito tim gero i gang",
            "Twero tito bot police onyo LC. Pe imito ye pa ngat ma otime.",
            "Peny namba me report. Legal aid twero woti kwedi.",
        ),
    ),
    "family-protection-orders": _all_langs(
        _pack(
            "Endagaano z'okukuumibwa",
            "Protection order ya kkooti eyinza okukomya eyakuyisa okukutuukako. Okugimenya kiyinza okuleeta okukwatibwa.",
            "Saba mu magistrate's court. Twaala obujulizi. Muweereze mu clerk.",
        ),
        _pack(
            "Protection order",
            "Court order ebeonokin stop lo contact kosi harm. Breach kewoto arrest.",
            "Kibo magistrate court. Ngot evidence. Kibo clerk.",
        ),
        _pack(
            "Cik me gwoko",
            "Protection order pa court twero gengo ngat me cobi. Keto woko twero kwako.",
            "Penyo i magistrate court. Cwal ngec. Peny clerk.",
        ),
    ),
    "family-property": _all_langs(
        _pack(
            "Eby'obugagga by'amaka",
            "Ettaka n'ennyumba y'amaka tebiba bya oyo yennyini erinnya ly'ekiwandiiko. Abafumbo balina eddembe.",
            "Land Act esaba okukkiriza kw'omufumbo nga ettaka ly'amaka ligulibwa. Weebuuze nga tonnawandiika.",
        ),
        _pack(
            "Property lo auren",
            "Land ka home pe lo name kere. Eongat ebeonokin ebeu.",
            "Land Act kewoto consent kane family land ejeni sale. Kibo legal aid.",
        ),
        _pack(
            "Jami pa gang",
            "Ngom ki ot pa gang pe pa nying i waraga kene. Monyom tye ki twero.",
            "Land Act mito ye pa monyom ka ngom me gang cato. Peny ma pe i coyo.",
        ),
    ),
    "family-spousal-property": _all_langs(
        _pack(
            "Eddembe ly'ettaka mu bufumbo",
            "Abafumbo balina eddembe lye kimu ku by'obugagga. Erinnya limu si nsonga yokka.",
            "Article 31 n'amateeka g'ettaka gakuuma. Tegeeza land office singa ettaka ligulibwa nga tokimanyi.",
        ),
        _pack(
            "Property lo eongat",
            "Ebeu lo property ejeni. Name kere pe ebeonokin nginar.",
            "Article 31 ka Land Act ebeonokin. Kibo land office kane sale pe ejeni.",
        ),
        _pack(
            "Twero pa monyom ku jami",
            "Monyom tye ki twero marom ku jami. Nying acel pe tum.",
            "Article 31 ki Land Act gwoko. Tito bot land office ka ngom cato ma pe ingeyo.",
        ),
    ),
    "family-wills": _all_langs(
        _pack(
            "Endagaano z'obufi",
            "Will kye kiwandiiko ekiraga nga eby'obugagga bwaabibwawo. Amateeka gateeka entegeka.",
            "Okukyusa will kyesigamizibwa ku mateeka, si ku kiwandiiko kyonna. Weebuuze mu ofiisi ya Administrator General.",
        ),
        _pack(
            "Will",
            "Will ebeonokin nginar lo property lo death. Succession Act ebeonokin form.",
            "Change lo will kewoto cik. Kibo Administrator General.",
        ),
        _pack(
            "Will",
            "Will aye waraga me poko jami ka to. Succession Act tero kit.",
            "Loko will myero lub cik. Cit bot Administrator General.",
        ),
    ),
    "family-inheritance": _all_langs(
        _pack(
            "Obusika",
            "Obusika bwe bufulumya eby'obugagga oluvannyuma lw'okufa, mu will oba mu ntegeka za intestacy.",
            "Succession (Amendment) Act, 2022 yakumye abafumbo n'abaana. Togabanya ettaka mu ngeri ey'amakambwe.",
        ),
        _pack(
            "Inheritance",
            "Inheritance ebeonokin property lo death, will kosi intestacy.",
            "Succession Amendment 2022 ebeonokin spouse ka ikoku. Pe kibo land lo force.",
        ),
        _pack(
            "Oneo",
            "Oneo aye poko jami ka ngat oto, ki will onyo ma pe tye will.",
            "Succession Amendment 2022 gwoko monyom ki litino. Pe pok ngom ki tek.",
        ),
    ),
    "family-intestacy": _all_langs(
        _pack(
            "Okufa nga tewali will",
            "Amateeka gassaawo abasika. Empisa tezimalawo ddembe ly'omufumbo n'abaana.",
            "Saba letters of administration. Tokwata nnyumba mu ngeri ey'amakambwe.",
        ),
        _pack(
            "Death pe will",
            "Intestacy ebeonokin shares lo cik. Custom pe ebeonokin wipe lo spouse.",
            "Kibo letters of administration. Pe kibo house lo force.",
        ),
        _pack(
            "To ma pe tye will",
            "Cik tero ngat ma oneo. Kwer pe ruc twero pa monyom ki litino.",
            "Penyo letters of administration. Pe kwany ot ki tek.",
        ),
    ),
    "family-probate": _all_langs(
        _pack(
            "Probate",
            "Probate buyinza bwa kkooti eri executor okukola ku by'omufu.",
            "Twaala will n'endagaano y'okufa ewa Administrator General. Togula ttaka nga tonnaba na buyinza.",
        ),
        _pack(
            "Probate",
            "Probate ebeonokin authority lo executor.",
            "Kibo will ka death certificate lo Administrator General. Pe kibo land sale.",
        ),
        _pack(
            "Probate",
            "Probate aye twero pa court bot executor.",
            "Cwal will ki waraga me to bot Administrator General. Pe cat ngom ma pe tye twero.",
        ),
    ),
    "family-letters-of-administration": _all_langs(
        _pack(
            "Amawandiike g'okuddukanya eby'omufu",
            "Letters of administration gaweereza omuntu okuddukanya eby'omufu nga tewali executor.",
            "Tandikira ewa Administrator General n'endagaano y'okufa.",
        ),
        _pack(
            "Letters of administration",
            "Letters kewoto authority kane executor pe ejeni.",
            "Kibo Administrator General ka death certificate.",
        ),
        _pack(
            "Letters of administration",
            "Letters miyo twero me tic ku jami ka executor pe.",
            "Cak bot Administrator General ki waraga me to.",
        ),
    ),
    "family-inheritance-disputes": _all_langs(
        _pack(
            "Enkaayana mu busika",
            "Enkaayana ku will, ennyumba oba omuddukanizi zisalibwa mu mateeka, si mu buyinza.",
            "Tereka caveat amangu. Funa legal aid so si nkelekele.",
        ),
        _pack(
            "Ajokot lo inheritance",
            "Dispute lo will kosi home ebeonokin cik, pe force.",
            "Kibo caveat. Legal aid kewoto, pe violence.",
        ),
        _pack(
            "Laro oneo",
            "Laro will onyo ot ngoo ki cik, pe ki tek.",
            "Ket caveat oyot. Nong legal aid, pe tim gero.",
        ),
    ),
    "family-guardianship": _all_langs(
        _pack(
            "Obulabirizi",
            "Omulabirizi ye alina obuyinza bw'amateeka okukuuma omwana. Si linnya ly'ekika kwokka.",
            "Saba mu kkooti y'abaana. Totwala mwana ku nsalo nga tewali ndagaano.",
        ),
        _pack(
            "Guardianship",
            "Guardian ebeonokin authority lo cik lo ikoku. Pe title lo auren kere.",
            "Kibo children court. Pe kibo ikoku lo border pe order.",
        ),
        _pack(
            "Gwoko latin i cik",
            "Guardian tye ki twero me cik me gwoko latin. Pe nying kaka kene.",
            "Penyo i court pa litino. Pe kela latin loka ma pe tye cik.",
        ),
    ),
    "family-adoption": _all_langs(
        _pack(
            "Okuyingiza omwana",
            "Adoption kusalawo kwa kkooti. Amateeka magumu, naddala ag'amawanga agalala.",
            "Tandikira ewa probation. Towanga ssente okufuna mwana.",
        ),
        _pack(
            "Adoption",
            "Adoption ebeonokin court order. Inter-country ebeonokin cik lo strong.",
            "Kibo probation. Pe kibo money lo ikoku.",
        ),
        _pack(
            "Keto latin i gang i cik",
            "Adoption aye cik pa court. Cik matek, dong ka loka.",
            "Cak bot probation. Pe cul cente me nong latin.",
        ),
    ),
    "family-foster-care": _all_langs(
        _pack(
            "Okukuuma omwana okw'ekiseera",
            "Foster care kuba okukuuma omwana okw'ekiseera nga gavumenti bwe ekiraba.",
            "Tuukirira probation. Tokola ntegeka z'ekyama eza 'okugula omwana'.",
        ),
        _pack(
            "Foster care",
            "Foster ebeonokin temporary care lo authority.",
            "Kibo probation. Pe kibo private sale lo ikoku.",
        ),
        _pack(
            "Gwoko latin pi kare",
            "Foster aye gwoko pi kare ma gavumenti neno.",
            "Cit bot probation. Pe ket ngec me wil latin.",
        ),
    ),
    "family-kinship-care": _all_langs(
        _pack(
            "Okukuuma kw'ab'oluganda",
            "Ab'oluganda bayinza okukuuma omwana, naye welfare n'amateeka bikwatawo.",
            "Tegeeza probation. Kinship tekuwa buyinza bw'obusika oba okutwala omwana ebweru.",
        ),
        _pack(
            "Kinship care",
            "Auren kewoto ikoku, welfare ebeonokin.",
            "Kibo probation. Kinship pe ebeonokin inheritance kosi border.",
        ),
        _pack(
            "Gwoko pa wat",
            "Wat twero gwoko latin, ento ber ki cik pud tye.",
            "Tito bot probation. Wat pe miyo oneo onyo kela loka.",
        ),
    ),
    "family-elder-care": _all_langs(
        _pack(
            "Okukuuma abakadde",
            "Abakadde balina eddembe n'ettaka. Okulekerera oba okwagala ettaka kuba kibi.",
            "Tegeeza poliisi oba legal aid. Okukuuma tekukuwanga ttaka.",
        ),
        _pack(
            "Care lo akiliok lo age",
            "Akiliok lo age ebeonokin dignity ka land. Abuse pe ejeni.",
            "Kibo police kosi legal aid. Care pe ebeonokin land grab.",
        ),
        _pack(
            "Gwoko lutino-ma-oti",
            "Lutino-ma-oti tye ki twero ki ngom. Weko onyo kwanyo ngom tye marac.",
            "Tito bot police onyo legal aid. Gwoko pe miyo ngom.",
        ),
    ),
}


FAMILY_SOURCE_I18N = {
    "Marriage Act": {
        "lg": "Ettwale ly'Obufumbo",
        "teo": "Cik lo Eongat",
        "ach": "Cik me Nyom",
    },
    "Customary Marriage (Registration) Act": {
        "lg": "Ettwale ly'Okwewandiisa Obufumbo bw'Ennono",
        "teo": "Cik lo Registration lo Eongat lo Kwer",
        "ach": "Cik me Coo Nyom me Kwer",
    },
    "Divorce Act": {
        "lg": "Ettwale ly'Okuggya Obufumbo",
        "teo": "Cik lo Divorce",
        "ach": "Cik me Keto Nyom Woko",
    },
    "Children Act": {
        "lg": "Ettwale ly'Abaana",
        "teo": "Cik lo Ikoku",
        "ach": "Cik me Litino",
    },
    "Domestic Violence Act, 2010": {
        "lg": "Ettwale ly'Obutabanguko mu Maka, 2010",
        "teo": "Cik lo Ajokot lo Auren, 2010",
        "ach": "Cik me Tim Gero i Gang, 2010",
    },
    "Succession Act": {
        "lg": "Ettwale ly'Obusika",
        "teo": "Cik lo Inheritance",
        "ach": "Cik me Oneo",
    },
    "Administrator-General's Act": {
        "lg": "Ettwale lya Administrator General",
        "teo": "Cik lo Administrator General",
        "ach": "Cik pa Administrator General",
    },
}


def translation_fields_for_topic(slug, lang):
    """Return field->text for a topic slug and language code, or {}."""
    block = FAMILY_TOPIC_I18N.get(slug, {}).get(lang) or {}
    if not block:
        return {}
    help_text = HELP_I18N[lang]
    docs = block.get("documents_required") or DOCS_I18N[lang]
    next_steps = block.get("next_steps") or help_text
    return {
        "name": block["name"],
        "title": block.get("title") or block["name"],
        "summary": block["summary"],
        "rights_information": block["rights_information"],
        "what_this_means": block.get("what_this_means") or block["summary"],
        "next_steps": next_steps,
        "documents_required": docs,
    }
