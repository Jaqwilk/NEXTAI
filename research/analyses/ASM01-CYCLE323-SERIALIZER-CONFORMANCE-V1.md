# ASM01 — cykl323: kompletna diagnoza i zgodność znanejT1

Zamknięto 2026-10-05T22:25:14Z; decyzja **KEEP wyłącznie techniczną naprawę serializera**.
Nowy EXP: **brak**. Niezmienny plan `research/plans/ASM01-SERIALIZER-STRUCTURE-PREPARATION-V1.json`, SHA256 `8db10c6c2bd714994b86f4b83e88593ef7e90a3ab15014c258cb2e8e88a2f8ae`,
oraz naprawa `research/plans/ASM01-SERIALIZER-METADATA-REPAIR-V1.json`, SHA256 `9b4d91cd42c681bf89c5dc42420a7d4f723a0de5f798674ce06825df92d04a86`.
120 minut, deadline2026-10-05T23:38:34Z,2200 s pomocniczych obliczeń;
zero rejestracji, fitu badawczego i scoringu. Cel rozszerzony pozostaje **ACTIVE**.

## OBSERVATION

Plan diagnozy zamrożono w512ffc3 przed implementacjąbebd502 i ponownym otwarciemT1.
Inwentaryzacja obejmuje wszystkie300 niepuste wiersze:290 wierszy punktów,
3PEN_DOWN,3PEN_UP oraz cztery wiersze nagłówka/count/kolumn/end. Wszystkie punkty
mają cztery pola całkowite i state1; trzy dodatnie numery kresek. PEN_DOWN ma
zero dodatkowych pól; każdy PEN_UP ma tylko **0**. X/Y nie konwertowano ani
nie wypisywano w diagnozie, nazwy znaków nie stały się kluczami. D/future/new0.

ParserV1 uznawał singleton w PEN_UP za bieżący dodatni numer kreski; dlatego0
powodowało poprzedni błąd. `categorical_serial_consistent=false` w niezmienionej
diagnozie obejmuje właśnie tę starą interpretację markera; nie jest osobnym
dowodem błędnego porządku punktów. Nowy kontrakt po diagnozie zamrożono w **e7f272e**
przed implementacją **d470518**. Minimalny adapterV4 usuwa tylko singleton0 z
PEN_UP w próbce z jednym poprawnie położonym dokładnym publicznym nagłówkiem.
Bez nagłówka i dla pozostałych form zachowujeV3. Całą walidację punktów, aktywnej
kreski, liczby kresek, caps, deduplikację i geometrię nadal wykonuje niezmienionyV1.

W niezależnym klonie **80/80 PASS**:49 nowych przypadków i31 niezmienionychV3.
Obejmują legacy, singleton0, nagłówki, numery/stan/współrzędne, pen lifecycle,
caps/ASCII i degenerację, dokładne punkty i wszystkie trzy deskryptory. Bez fitu.

Pierwsze uruchomienie native conformance zatrzymało się **PRZED utworzeniem Job,
otwarciem stdout/stderr lub procesu potomnego**: rezerwacja trwała32.47 s i dla
checkcap90/overhead65 pozostał niedodatni timeout. Zachowano pełny błąd i73 s.
Prospektywny append-only addendum zwiększył tylko cap pojedynczego nadzorowanego
uruchomienia do160/timeout90 w tych samych2200 s i deadline; kod, dane, nauka,
fikstury i wszystkie stare capy/gates nie zostały zmienione. Nie było pierwszej
próby native parsera ani retry płatnego EXP. KontrolaV2 jest pierwszym uruchomionym
procesem conformance po tej naprawie administracyjnej.

Dokładnie jedna już ujawnionaT1,10644 B, SHA256
`4c3e65ac49ff5ad55f521ab9f86b47dbaa55cfb5cd341d6d1d234ad1d4e9dfff`:
**PASS**,290x2 float32,290 surowych wierszy punktów. Cała tablica równa niezależnemu
odczytowi punktów z oryginalnych wierszy z resetem na granicy kreski; trzy64D
deskryptory write/nominal/adverse identyczne bitowo i skończone. W jednym procesie
wywołano takżeV3 jako kontrolę odtworzonej awarii i niezależny odczyt referencyjny;
nie oznacza to tylko jednej operacji konwersji każdej liczby. Częściowy odczyt
punktów kontrolnegoV3 nie był instrumentowany. Wypisano tylko counts/shapes/hashes,
bez współrzędnych lub nazw. Nowe próbki0,D0,ekstrakcja0,NPZ0,fit0,scoring=false.

Oryginalny startup/closing doctor i startup lab: PASS. Klon: lifecycle **1/1 PASS**,
pełny CLI lab errors=[],warnings=[]. Wszystkie wykonane Job trees zamknięte bez
żywych potomków. Aktualny manifest **1436 plików**; wszystkie
1434 wcześniejsze chronione bajty poza pięcioma uprawnionymi metadanymi zachowane.
Stare nagłówki, plany, wyniki, parseryV1/V2/V3 i źródła/model/generator pozostają
niezmienione. Pełna regresja nie była powtórzona; timeout46% z321 nadal niezaliczony.

## INTERPRETATION

Usunięto konkretną pomyłkę serializacji bez zmiany numerycznej reprezentacji.
Nie uzyskano nowego wyniku naukowego: brak nowych efektów jakości,rankingu,
aktualizacji,UNKNOWN,transferu albo ekonomii. Żadne testy techniczne nie zastępują
kompetentnej kontroli Transformer ani niezależnych pięcioparowych wyników.
EXP-20261005-0007 pozostaje DISCARD dla dokładnej receptury source-transfer HAR,
z ekonomią INCONCLUSIVE przy niekompetentnej kontroli dense.

## CONFIDENCE

Wysoka dla tej dokładnejT1 i deklarowanych syntetycznych reguł. Niepewność dotyczy
formatu i degeneracji pozostałych autorów; jedna już znana próbka nie potwierdza
całego zbioru. Nie ma nowych naukowych przedziałów ufności ani twierdzenia o transferze.

## ALTERNATIVE EXPLANATIONS

PEN_UP0 to jawny marker zamknięcia, a nie punkt z zerowym numerem kreski. Sposób
kodowania innych markerów pozostaje objęty dawną ścisłą walidacją; nowe nieznane
formy powinny zatrzymać osobny intake. Zmiana geometrii, wybór łatwiejszych autorów
lub pomijanie próbek nie są naprawą metadanych i nie zostały wykonane.

## DECISION

**KEEP wyłącznie techniczną naprawęV4**, bez promocji i bez gotowości do scoringu.
Prospektywny task `research/plans/ASM01-VERIFIED-SERIALIZER-TASK-V3.json`, SHA256 `d34bf101fe22ad5fbe739d6ff05a24b96ce4939eca57720f76b8eb89063c4dd1`,
wiąże naprawę iT1, z `execution_authority=false`. Comparison/metrics/training/views/
independent_units są identyczne z taskV2; jawnie ujawniono znanąT1 i zachowano
nieudane intakeV1/V2. Osobny naukowy kontrakt i nowy cohort są nadal konieczne.

| Rozliczenie append-only | Sekundy |
|---|---:|
| NEXTAI-B-323-startup-doctor | 217 |
| NEXTAI-B-323-startup-lab | 257 |
| NEXTAI-B-323-administration-prepaid | 300 |
| NEXTAI-B-323-T1-structural-diagnosis-V1 | 54 |
| NEXTAI-B-323-serializer-fixtures-V1 | 57 |
| NEXTAI-B-323-T1-serializer-conformance-V1 | 73 |
| NEXTAI-B-323-T1-serializer-conformance-V2 | 59 |
| NEXTAI-B-323-maintenance-seal-V1 | 148 |
| NEXTAI-B-323-closing-doctor-V1 | 234 |
| NEXTAI-B-323-clone-lab-lifecycle-V1 | 383 |

Łącznie **1782/2200 s**, w tym awaria przed Job, wszystkie testy,
pełne czasy kontroli i konserwatywne allowance. Administration300 s obejmuje
prereads, kontrakty/skrypty administracyjne, archiwum, mirror/raport/Git; nie ukrywa
diagnozy, parsera lub testów. B **1/12**, **14185.550240200/72000 s**;
pozostało 57814.449759800 s, w tym chronione **7 rejestracji/47000 s**.
Swobodny margines 10814.449759800 s. A zamknięty11/17,35649.98936010008 s;
MUC03 zamknięty3/2655.336484700005 s; niewydaneA nie powiększaB. Wszystkie rezerwacje
rozliczone, maintenance, ready=false, scoring=false; snapshots seal/CLI mogły
obejmować bieżącą wtedy rezerwację, końcowe liczby pochodzą z rozliczonego ledgeru.
Bez WT8–9, zewnętrznych modeli/API, zmiany harmonogramu i płatnego retry.

## NEXT DISCRIMINATING EXPERIMENT

Freeze ASM01-FROZEN-SOURCE-SCREEN-V3 in a NEW bounded cycle using the prospective verified-serializer taskV3: exact existing source states/models,4096pairs/2048alignment/1024decoder, all9arms,five predefined disjoint writer pairs,K16/32/64,updates0/1/4,nominal/adverse and unchanged metrics/grids/quality/UNKNOWN/FA/economic gates. Pin remaining budget/future reserve and original intake failures/exposed-T1. Implement only delegated new-cohort/loader/acquisition wrappers, validate in independent clone before remaining native T/D content; complete all1830 screen samples without dropping/replacing failures;freeze/preflight/readiness before exactly one audited EXP. No paid retry.

Transfer drugiej rodziny, niezależne replikacje, świeży finał i lokalny prototyp
fact/source/update/UNKNOWN nadal wymagają wykonania. Cel nie jest ukończony.
