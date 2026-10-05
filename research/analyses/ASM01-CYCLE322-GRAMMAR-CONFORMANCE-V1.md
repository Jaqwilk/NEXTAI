# ASM01 — cykl322: zgodność nagłówka i nieudana próbka natywna

Zamknięto 2026-10-05T21:33:48Z. Nowy EXP: **brak**; niezmienny plan `research/plans/ASM01-NATIVE-GRAMMAR-CONFORMANCE-V1.json`,
SHA256 `2e33af01acf0fee203275a84f434279de6c5f098a6ee2178bc87fd994b7ea217`. 90 minut, deadline 2026-10-05T22:08:28Z,
1800 s pomocniczych obliczeń, zero rejestracji, fitu badawczego i scoringu.
Szerszy cel pozostaje **ACTIVE**; ostatni wynik naukowy to EXP-20261005-0007.

## OBSERVATION

Prospektywny commit263c817 poprzedził implementację8993bca oraz każdy nowy test
i konwersję T1. Adapter21 linii usuwa wyłącznie jeden dokładny publiczny nagłówek
`X Y STYLUS_STATE STROKE` w zadeklarowanym miejscu, a następnie deleguje do
niezmienionego parseraV1. Zachowuje byte cap przed usunięciem, numeric/stroke rules,
deskryptory, modele, metryki, progi, siatki klasyczne i stare plany/wyniki.

Pierwszy przebieg31 przypadków miał **2 błędy infrastruktury setup/teardown**,
zero failures: pytest umieścił ponad256KiB parametru bytes w identyfikatorze testu
i przekroczył limit zmiennej środowiskowej Windows. Pozostałe30 przypadków przeszło.
Zachowano surowe logi/JUnit i dokładne źródło testu. Commit834f3fc zmienił tylko
krótkie jawne identyfikatory, bez payloadów, asercji lub parsera; skorygowany
przebieg w niezależnym klonie: **31/31 PASS**. To testy syntetyczne bez fitu.

Dokładnie jedna już ujawniona próbkaT1,10644 B, SHA256
`4c3e65ac49ff5ad55f521ab9f86b47dbaa55cfb5cd341d6d1d234ad1d4e9dfff`,
pozostała jedynym legalnym plikiem natywnym. V1 nadal odrzuca nagłówek jako
`Native point grammar`. Adapter przeszedł nagłówek, lecz ścisła walidacjaV1
zatrzymała się na **`ValueError: Pen-up supplied state/stroke`**. Nie zwrócono
tablicy ścieżki ani żadnego z trzech deskryptorów. W tym cyklu podjęto autoryzowaną
konwersję liczbT1; liczba częściowo przekonwertowanych punktów **nie była
instrumentowana i jest nieznana**. Nie wolno raportować jej jako zero.
Nowe próbki0, numeryczny dostępD0, nowa ekstrakcja0, NPZ0, fit0, scoring=false.
Nie wykonano naprawy ani ponownej próby natywnej po tym błędzie.

Startup doctor i lab oraz końcowy doctor: PASS. Końcowa kontrola niezależnego
klonu: test lifecycle **1/1 PASS**, pełny CLI lab status errors=[],warnings=[].
Wszystkie drzewa procesów zamknięte, brak żywych potomków. Bieżący manifest
**1434 pliki**; wszystkie1432 wcześniejsze chronione bajty poza pięcioma jawnie
uprawnionymi metadanymi zachowane; stare nagłówki zachowane dosłownie w archiwum.
Pełny zestaw regresji nie został wykonany ponownie; timeout46% z cyklu321 pozostaje
niezaliczonym historycznym przebiegiem, a nie dowodem pełnego pokrycia.

## INTERPRETATION

Potwierdzono wąską obsługę nagłówka w syntetycznych fiksturach. Nie potwierdzono
zgodności całego serializera wydawcy: następny warunekPEN_UP różni się od przyjętej
gramatyki. Nie uzyskano nowego wyniku jakości, UNKNOWN, aktualizacji, transferu
ani kosztu end-to-end; brak nowych estymacji i przedziałów ufności naukowych.
Awaria techniczna nie falsyfikuje architektonicznej rodziny. Ujemny wynik dokładnej
recepturyHAR w EXP-20261005-0007 oraz niekompetentna kontrola dense pozostają bez zmian.

## CONFIDENCE

Wysoka dla konkretnego odtworzonego błędu i zachowania historii. Zgodność pełnej
natywnej gramatyki pozostaje niepotwierdzona; jedna widoczna próbka nie gwarantuje
formatu innych autorów. Nie ma podstaw do ilościowej pewności transferu lub ekonomii.

## ALTERNATIVE EXPLANATIONS

Dotychczasowe fikstury odzwierciedlały założoną semantykęPEN_UP, a nie pełny
serializer wydawcy. Należy jednocześnie zinwentaryzować wszystkie rodzaje wierszy
już znanejT1 przed kolejną implementacją. Możliwe są dalsze różnice serializacji;
nie należy zgadywać kolejnego pola ani otwierać świeżych danych w zamkniętym etapie.

## DECISION

**INCONCLUSIVE** dla natywnej zgodności i wszystkich twierdzeń naukowych.
Nie spełniono prerejestrowanej reguły KEEP adaptera jako kompletnej naprawy.
Zachować wąską obsługę nagłówka i wszystkie niepowodzenia jako historię techniczną;
bez promocji, gotowości do scoringu lub ratowania starego intake po wyniku.

| Rozliczenie append-only | Sekundy |
|---|---:|
| NEXTAI-B-322-startup-doctor | 220 |
| NEXTAI-B-322-startup-lab | 259 |
| NEXTAI-B-322-administration-prepaid | 300 |
| NEXTAI-B-322-clone-grammar-fixtures-V1 | 55 |
| NEXTAI-B-322-clone-grammar-fixtures-V2 | 55 |
| NEXTAI-B-322-exposed-T1-conformance-V1 | 55 |
| NEXTAI-B-322-maintenance-seal-V1 | 141 |
| NEXTAI-B-322-closing-doctor-V1 | 217 |
| NEXTAI-B-322-clone-lab-lifecycle-V1 | 373 |

Łącznie **1675/1800 s**, w tym nieudane testy i native conformance,
pełne czasy nadzoru/CLI oraz konserwatywne allowance. Administration300 s obejmuje
prereads, prerejestrację, zachowanie archiwum, mirror, raport końcowy i Git;
substantywne kontrole są dodatkowo rozliczone. Zero fitu badawczego i płatnych prób.
B: **1/12**, **12403.550240200/72000 s**;
pozostało 59596.449759800 s, w tym chronione **7 rejestracji/47000 s**. Swobodny
margines 12596.449759800 s. A pozostaje zamknięty11/17,35649.98936010008 s;
MUC03 zamknięty3 prób,2655.336484700005 s. NiewydaneA nie powiększaB.
Wszystkie rezerwacje cyklu rozliczone, maintenance, ready=false, scoring=false.
Snapshot CLI/seal mógł obejmować wtedy bieżącą rezerwację; liczby końcowe wyżej
pochodzą z rozliczonego ledgeru. WT8–9, harmonogram i modele/API zewnętrzne bez zmian.

## NEXT DISCRIMINATING EXPERIMENT

Preregister a bounded structural serializer diagnosis of ONLY the already-exposed T1: inventory all header/pen/numeric-row token counts and categorical marker conventions without coordinate values, new files or fit. Then prospectively freeze the complete justified grammar repair before implementation, preserve numeric bounds/geometry/models/gates, validate synthetic fixtures and T1 in the clone. Only after success freeze a NEW scientific intake/cohort before fresh native feasibility, independent clone/preflight/readiness and one audited five-pair three-scale nominal/adverse experiment. No paid retry or one-field rescue in closed cycle322.

Przyszłe replikacje, świeży finał i minimalny prototyp fact/source/update/UNKNOWN
pozostają niewykonane. Zamknięcie tego przygotowania nie zamyka całego celu.
