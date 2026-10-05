# ASM01 — cykl 321: nieważne przygotowanie native intake

Zamknięto 2026-10-05T20:30:01Z. **INCONCLUSIVE**: intake zatrzymano przed fit badawczym,
realizacją prywatnych jednostek/seedów, rejestracją płatną i scoringiem. Nie uzyskano
nowego wyniku jakości, transferu ani ekonomii. Szerszy cel pozostaje **ACTIVE**.

## Identyfikator, kontrakty i proweniencja

Nowy EXP: **brak**; ostatni wynik nadal EXP-20261005-0007. Niezmienny plan V2:
`research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json`, SHA256 `ff35bd63a84ce510fc13e67f5d1f5314620607a634899aa321d74c2d39411925`; task:
`research/plans/ASM01-CANONICAL-NATIVE-TASK-V2.json`, SHA256 `debdeea304bec803b482c421b6d7d54dfc398a8563f7312f7a84fdbe226063a9`. Plan V1 pozostaje
`research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json`, SHA256
`eeed8e364291320100eaf10d54788cbb29b1407b92fdf95aa0f85f257c08fa4e`.
Wspólny początek 2026-10-05T18:50:32Z, deadline 2026-10-05T21:50:32Z,
180 minut, 3600 s pomocniczych obliczeń, 9000 s łącznego pełnego kosztu workerów
i najwyżej jedna rejestracja. W tym cyklu **0/1** nowych rejestracji i **0 s** fitu badawczego.

V1 zamrożono w 05ba675 przed implementacją i odczytem współrzędnych; publiczne
syntetyczne testy i przygotowany kod w 3d21ffa poprzedziły archiwum. V2 zmieniła
jedynie kanoniczne członkostwo zbioru na podstawie nazw/rozmiarów archiwum,
przed otwarciem próbki. Cały przygotowany cohort i testy zamrożono w 3cfae7f przed
intake V2. Formalny późniejszy event study_frozen wiąże status terminalnego intake
z tą wcześniejszą prerejestracją; nie jest dowodem nowego prospektywnego freeze po wyniku.
Modele, 4096 par, receptury, metryki, progi, siatki i wspólne capy nie zostały zmienione.

## OBSERVATION

Publiczny [zbiór UCI Assamese](https://archive.ics.uci.edu/dataset/208/online+handwritten+assamese+characters+dataset),
Baruah/Hazarika2015, DOI10.24432/C50C8Q, CC BY4.0, stanowi niezależną rodzinę
natywnych pomiarów pióra wobec HAR. Jedyny download: **8 067 448 B**, publisher
SHA256 `d6ad543e65269d53e38fdac6a32dd20bcd942e7616891a6cf95986894b454a4d`.
Całe archiwum: 8237 plików, w tym 8236 TXT i nieotwarty Data_Table.pdf,
66 920 184 B deklarowanej zawartości po rozpakowaniu.

V1 wykryła dodatkową obcą ścieżkę W6/15.5.TXT, 9459 B, dotyczącą autora5,
obok właściwego W5/15.5.TXT, 5572 B. Zatrzymała się na indeksie archiwum przed
ekstrakcją/liczbami. Przerejestrowana korekta V2 wyklucza wyłącznie tę obcą ścieżkę:
**45 autorów ×183 kanoniczne pliki =8235**, zero brakujących natywnych próbek,
bez zastępowania lub usuwania kanonicznych autorów. Nie pobrano archiwum ponownie.

V2 wyodrębniła tylko screen T1–5/D16–20. Pierwsza próbka T1/sample1 zatrzymała
ścisły parser na linii3: tekstowy nagłówek **X Y STYLUS_STATE STROKE** został
potraktowany jak wiersz punktu liczbowego. Bajty tej próbki **zostały otwarte**;
nie wolno opisywać tego jako braku dostępu do zawartości natywnej. Pierwszy błąd
wystąpił przed konwersją punktów liczbowych i zwróceniem deskryptorów; numerycznych
plików D nie przetworzono. Dodatkowa diagnoza czytała wyłącznie już ujawnioną
pierwszą próbkę, zapisała nazwy pól i zredagowała wartości liczbowe. Nie zmieniono
parsera ani naukowej receptury po tym odczycie. Przyszli autorzy replikacji/finału
nie byli wyodrębniani ani przetwarzani numerycznie. Brak NPZ gotowego screeningu.

Przygotowano minimalny parser, deterministyczne dwa widoki 32-punktowe/64D,
aktualizowalną pamięć z bieżącą wartością i źródłem, scoring UNKNOWN z kalibracją
tylko na T, import rzeczywistych stanów trained/untrained/shuffled/ridge ze źródła,
niezmienny dense i mocne ridge/PCA/kernel/raw/DTW. Pięć par, K16/32/64,
aktualizacje0/1/4, nominal/adverse. To przygotowany kod zweryfikowany na fiksturach,
**nie wykonany eksperyment natywny**. Stare modele HAR/PVM są niezmienione.

Przed zawartością przeszły16 przypadków V1,5 kanonicznych i28 pełnego cohortu.
Końcowe testy objęte zmianą: **28 PASS**, jedyny błąd w przebiegu29 przypadków
dotyczył starego wygenerowanego research/REPORT.md w klonie. Po odświeżeniu
tego raportu pojedynczy test lifecycle zakończył się **1/1 PASS**.
Pełny CLI `uv run --no-sync nextai lab status` w niezależnym klonie: **PASS**,
errors=[], warnings=[], bez potomków pozostających po zakończeniu procesu.
Doctor w oryginale na początku cyklu: PASS. Początkowy lab status FAIL wykrył
brak jeszcze niezamrożonych nowych ASM plików w starym manifeście; zachowano ten wynik.

Pełny zestaw regresji: **TIMEOUT**, ostatni zapisany postęp46%, brak kompletnego
JUnit. Nie jest to zaliczony przebieg. Utrwalono stdout/stderr, nadzorowane drzewo
procesów i oddzielny dowód, że po zamknięciu Job nie pozostały wskazane procesy.
Nie powtórzono pełnego zestawu, płatnego eksperymentu ani realizacji seedów.

## INTERPRETATION i CONFIDENCE

**INCONCLUSIVE** dla skuteczności i kosztów: brak porównań natywnych, brak
przedziałów ufności jakości/transferu i brak mierzalnej przewagi end-to-end.
Wysoka pewność dotyczy konkretnego błędu zgodności parsera z publicznym nagłówkiem,
kanonicznego indeksu oraz zachowania historii. Awaria nie falsyfikuje rodziny
architektur ani transferu. Zamrożona reguła zatrzymania intake pozostaje spełniona;
V1/V2 nie wolno ratować zmianą parsera i kontynuacją scoringu pod starym planem.

Wcześniejszy EXP-20261005-0007 nadal stanowi ujemny wynik tej dokładnej receptury
source-transfer HAR, z nierozstrzygniętą ekonomią przy niekompetentnej kontroli dense;
nie zamieniono go w wynik dodatni przez wybór innego zbioru. Nowe przygotowanie
ASM nie dostarcza nowego dowodu. Replikacje, świeży finał i prototyp użytkowy
fact/source/update/UNKNOWN nadal wymagają wykonania.

## Integralność, koszty i awarie

| Rozliczenie append-only | Sekundy |
|---|---:|
| NEXTAI-B-321-startup-doctor | 222 |
| NEXTAI-B-321-administration-prepaid | 300 |
| NEXTAI-B-321-closed-archive-compression | 325 |
| NEXTAI-B-321-startup-lab | 259 |
| NEXTAI-B-321-precontent-conformance-V1 | 58 |
| NEXTAI-B-321-native-intake-V1 | 64 |
| NEXTAI-B-321-intake-header-diagnosis-V1 | 55 |
| NEXTAI-B-321-canonical-precontent-conformance-V1 | 55 |
| NEXTAI-B-321-canonical-precontent-conformance-V2 | 55 |
| NEXTAI-B-321-cohort-precontent-conformance-V1 | 60 |
| NEXTAI-B-321-canonical-native-intake-V1 | 56 |
| NEXTAI-B-321-maintenance-seal-V1 | 143 |
| NEXTAI-B-321-clone-full-regression-V1 | 576 |
| NEXTAI-B-321-affected-conformance-V1 | 102 |
| NEXTAI-B-321-clone-lab-lifecycle-V2 | 372 |
| NEXTAI-B-321-closed-mirror-V1 | 57 |

Łącznie **2759/3600 s**, w tym wszystkie nieudane testy, intake,
ewaluacje fikstur, nadzór i konserwatywne allowance. Fikstury zawierają małe
syntetyczne fit/readout/optimizer checks, obciążone powyżej; **0 s fitu badawczego**
nie oznacza braku każdej operacji treningowej w testach. Rezerwa administracyjna
300 s obejmuje sporządzanie dokumentów, diag już ujawnionego T1, mirror i Git;
nie pomija pracy naukowej ani obliczeń zakończonych błędem.

B: **1/12 rejestracji**, **10728.550240200/72000 s**;
pozostaje 61271.449759800 s, w tym chronione **7 rejestracji/47000 s** na niezależne
replikacje, świeży finał i prototyp. Swobodny margines: 14271.449759800 s.
A zamknięty11/17 i35649.98936010008 s; wcześniejszy MUC03 zamknięty3 rejestracje/
2655.336484700005 s. Nie przeniesiono niewydanego A do B. Snapshot CLI klonu
obejmował nierozliczoną wtedy rezerwację450 s; końcowe liczby tutaj pochodzą z
rozliczonego append-only ledgeru. Wszystkie rezerwacje cyklu są rozliczone;
paid pending=false, maintenance, scoring=false, ready=false.

Porównano **1523 plików** w obu checkoutach; aktualne manifesty
1432 plików PASS. Poprzednie plany, wyniki, analizy, source-state ZIP i rejestry
zachowują bajty. Uprawnione zmiany harnessu i metadanych mają archiwum rodzica;
historyczne wpisy baseline i klauzule schematu pozostały identyczne. Nie ma nowego
EXP. Nie zmieniano WT8–9, harmonogramu, modeli zewnętrznych ani progów ekonomicznych.

Zachowane awarie: startup lab, V1 duplicate-member intake, pierwsza kanoniczna
fikstura z błędem importu podczas kolekcji, V2 native point grammar, pełna regresja
timeout i nieaktualny raport w29-case check. Żaden wynik nie został usunięty.

Kompresja zamkniętych własnych archiwów NTFS LZX zachowała4725 ścieżek i hashe
zawartości, zero usunięć, odzyskała **11991678976 B**.
Narzut odczytu/dekompresji nadal należy do pełnej granicy pomiaru; nie zmieniono
historycznych czasów. Wolne miejsce przy zamknięciu: **15558799360 B (14.490 GiB)**.
Brama10 GiB po przyszłym maksymalnym footprint320 MiB: **PASS**;
to migawka, wymagająca ponownego pomiaru przed instalacją/download.

## DECISION i NEXT DISCRIMINATING EXPERIMENT

**INCONCLUSIVE; zamknięcie nieudanego intake V1/V2, bez promocji i bez zamknięcia
całego celu.** Zachować recepturę i alternatywy; parser wymaga odrębnej prospektywnej
naprawy technicznej z nową wersją cohortu przed kolejnymi danymi.

Następny cykl: prerejestrowana naprawa wyłącznie publicznego nagłówka czterech
kolumn; odrzucanie błędnych/powtórzonych/przesuniętych nagłówków, syntetyczne
fikstury i tylko już ujawniony T1 w klonie, bez scoringu lub nowych próbek.
Następnie osobny freeze nowego intake/receptury, walidacja natywnej wykonalności,
integrity/preflight/readiness i dokładnie jeden audytowany EXP z pięcioma parami,
trzema skalami oraz pełnymi kontrolami. Wszystkie dotychczasowe capy i koszty
pozostają zużyte. Nie jest to retry płatnego EXP ani zmiana V1/V2 po wyniku.
