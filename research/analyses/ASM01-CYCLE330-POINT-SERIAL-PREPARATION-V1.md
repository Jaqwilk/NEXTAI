# ASM01 — cykl330: normalizer punktowych seriali

## OBSERVATION

Prerejestracja cf7faa8 przed implementacją i danymi; source freeze3a86e52 przed
jedyną walidacją niezależnego klonu. Dokładnie38przypadków:8accept,20reject,
4caps,6invariants. Wynik: {'errors': 0, 'failures': 0, 'skipped': 0, 'tests': 38}. Decyzja **KEEP technical normalizer only**.
Kod nie jest zintegrowany z aktywnym loaderem/parserem; dotychczasowe źródła,
modele, geometria, metryki, progi, wyniki i błędy pozostają niezmienione.

Normalizer przyjmuje wyłącznie kwalifikowany format release. Jawne monotoniczne
seriale wyznaczają grupy; zachowuje każdy punkt i kolejność oraz wszystkie puste
stroke1..N. X/Y pozostają tokenami; jedyny alias to literalne-0→0. Znane bareDOWN
iUP0 traktuje jako adnotacje. Inne wiersze/markery odrzuca. Emisja bareDOWN/bareUP
jest formatem legacy dla dokładnie zachowanegoV4; nie deklarujemy idempotencji.
Pełny rozmiar jest sprawdzany przed materializacją. Bez nowych nativebytes,
konwersji native, NPZ, fitu, rejestracji lub EXP.

## INTERPRETATION

Testy wykazały zachowanie syntetycznych starych tablicfloat32 i wszystkich trzech
deskryptorów write/nominal/adverse, także przy duplikatach na granicy stroke
i pustych identyfikatorach. Pułapka konwersji X/Y i kontrola AST potwierdzają
oddzielenie metadanych od geometrii. Dokładne prefiksy3ledgerów i parenthashes
zachowane. Procesy nadzorowane zakończone bez żywych potomków.

## CONFIDENCE

Wysoka dla deklarowanego skończonego zakresu syntetycznego, bez wniosków o
uczeniu, transferze lub ekonomii. Zgodność74 dawnych nativearrays i pełna
wykonalność1830próbek pozostają **NIEZWERYFIKOWANE**. Histogram nie dowodzi
monotoniczności rzeczywistych seriali ani tego, że podpisaneY są literalnym-0.

## ALTERNATIVE EXPLANATIONS

Możliwy niezerowy signedY, nieporządek seriali, zmiana deduplikacji lub
degeneracja geometrii zamkną tę dokładną trasę w późniejszym intake. Nie wolno
stosowaćabs/clamp/offset, usuwać punktów, próbek lub niekorzystnych jednostek.
Niezależny przegląd przedrunem domknął dwie luki pokrycia w tych samych namedcases;
V1draftbytes i V1/V2bindings zachowano. Nie było nieudanej próby testowej ani retry.

## DECISION

KEEP wyłącznie techniczny artefakt. NaukowoINCONCLUSIVE, scoring=false.
Pełny koszt od03:12:30Z: konserwatywnie **889/1200s**, pomiar do rozliczenia
738.386s, z buforem końcowej administracji. Fit0/EXP0. Koszt joba jest
zagnieżdżony w pełnym zegarze; nie sumujemy go ponownie. B:
22132.550240/72000s,1/12rejestracji;
chronione7/47000, marginesniechroniony2867.449760s.
Zachowano wcześniejszy Labtimeout180s, bez jego powtórzenia.

## NEXT DISCRIMINATING EXPERIMENT

Przed dalszymi bytes potrzebny nowy dokładny, opłacony kontrakt: SHA-bound
stare74parsowanieV4 i porównanie tablic/all3views; wszystkie1830próbki bez
filtrowania oraz niezmienione bounds/dedup/pointcap/geometry/view gates.
Przyszły wrapper ma jawnie zachować legacyobsługę; nie może używać fallbacku
do ukrycia różnicy dawnej zaakceptowanej tablicy. Obecne10800s rezerwacji
pełnego screeningu nie mieści się w marginesie. Niższy kompletny cap wymaga
oddzielnego uzasadnienia kosztów, z wszystkimi45rolami/810trials i bramkami;
przekroczenie zatrzyma niedokończony zakres. Nie finansujemy go rezerwą47k.

Cel drugiej rodziny transferu, niezależnych replikacji, świeżych finałów i
minimalnego lokalnego prototypu fact/source/update/UNKNOWN pozostaje ACTIVE.
Dowody: research/laboratory/ASM01-POINT-SERIAL-PREP-COMPLETION-V1.receipt.json
oraz losslessarchive z bindingami źródeł i surowych wyników.
