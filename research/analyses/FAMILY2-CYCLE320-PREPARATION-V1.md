# FAMILY2 — przygotowanie cyklu 320

Zamknięto 2026-10-05T18:41:37Z. Decyzja: **KEEP warunkową propozycję niezależnej rodziny ASM01**;
nie uzyskano nowego wyniku uczenia, transferu ani ekonomii. Szerszy cel pozostaje aktywny.

## Identyfikator i niezmienny plan

Nowy EXP: **brak**; zero rejestracji i zero fitu badawczego. Ostatni ukończony wynik
pozostaje EXP-20261005-0007. Plan przygotowania: `research/plans/NEXTAI-FAMILY2-INTAKE-PREPARATION-V1.json`,
SHA256 `dc8d6b48cad1872fb9047b99d05f573c32a348003a9139855599c6119579cfa5`; zamrożenie w Git 554a76c przed odczytem metadanych.
Początek 2026-10-05T17:32:51Z, deadline 2026-10-05T19:32:51Z, cap 120 minut/1800 s
testów i pomocniczych obliczeń. Zamknięte plany, wyniki, progi i historyczne awarie zachowano.

## OBSERVATION — co sprawdzono

Porównano wyłącznie metadane trzech publicznych źródeł. Przetworzone optdigits mają
64 wejścia i klasę, bez identyfikatora autora w wierszu: odrzucamy ten sposób intake dla
protokołu wymagającego 15 niezależnych par. Oryginalne nagłówki pozostają niezbadane;
nie dowodzimy niemożliwości całego zbioru. [Dokumentacja UCI](https://archive.ics.uci.edu/ml/machine-learning-databases/optdigits/optdigits-orig.names).

NIST SD19 `by_write` dokumentuje autorów, ale zapisany prefiks katalogu ZIP jest częściowy:
13 038 wpisów z 830 019; nie potwierdza liczności wszystkich wybranych autorów. Pozostaje
też niewyjaśniona stosowalność konkretnych warunków licencyjnych SD19. To zachowana
alternatywa, nie aktualna rodzina. [NIST](https://www.nist.gov/srd/nist-special-database-19),
[przewodnik](https://s3.amazonaws.com/nist-srd/SD19/sd19_users_guide_edition_2.pdf).

UCI Online Handwritten Assamese Characters dokumentuje **45 autorów po 183 natywne
trajektorie**, jawne numery autorów w katalogach i nazwach oraz **CC BY4.0**. Jest to
inna rodzina fizycznych pomiarów niż inercyjne HAR. [Oficjalne metadane i licencja](https://archive.ics.uci.edu/dataset/208/online+handwritten+assamese+characters+dataset).
W bieżącym cyklu nie pobrano ani nie odczytano współrzędnych, obrazów ani etykiet próbek.
Zapisano 1 643 227 B nazw/opisów/katalogu ZIP, poniżej 4 MiB capu. Dokładna długość RAR
pozostaje nieznana: HEAD nie podał Content-Length; 7.7 MB to oszacowanie wydawcy.
Surowe bajty i odzyskany opis mają osobne hashe; odzysk nie wykonywał nowych requestów.

Prospektywny dokument `research/plans/ASM01-PROSPECTIVE-NATIVE-TASK-V1.json` ma SHA256 `218d7a5d7fd0efb748341f76a4d83fb2e62ab793136382888ef241d877872360`.
Przypisuje T1–5/D16–20 do screeningu, T6–10/D21–25 do niezależnej replikacji,
T11–15/D26–30 do świeżego finału; 31–45 pozostają niewykorzystani. Pięć par,
K16/32/64, aktualizacje0/1/4, warunki nominal/adverse. To pamięć konkretnych instancji,
nie OCR ani dowód transferu semantycznego. Dwa widoki są zależnymi podpróbkami jednej
trajektorii, nie niezależnymi akwizycjami. Przewidziano rzeczywiste zamrożone stany źródła
oraz kontrole untrained/shuffled z identyczną dozwoloną adaptacją, kompetentny dense,
ridge/PCA, kernel, raw i band4 DTW na tych samych publicznych widokach. Kalibracja score
plus margin będzie używać wyłącznie treningu, bez ratowania zamkniętego HAR dev.

Pełny doctor i CLI lab status w oryginale **PASS**; pełny CLI lab status w niezależnym
klonie **PASS**, bez błędów i ostrzeżeń. Końcowe 39/39 przypadków pytest **PASS**, proces
zakończył się kodem0. Oddzielnie przeszły dwa syntetyczne przypadki HEAD: długość brakująca
oraz jawna1234; nie użyto sieci ani danych docelowych. Zweryfikowano 1370 wcześniejszych
plików chronionych, zachowanie prefiksów ledgerów i dosłownych historycznych dokumentów.
Dowód końcowego lustrzanego zapisu porównał 1449 plików; oryginał i
klon mają też niezmienny natywny wynik EXP-20261005-0007 i archiwum faktycznych stanów źródła.
Kod src, kandydaci, testy i schematy nie zostały zmienione w tym cyklu.

## INTERPRETATION i CONFIDENCE

KEEP dotyczy wyłącznie udokumentowanej, ograniczonej propozycji zadania. Pewność co do
publikowanych liczności/licencji/proweniencji jest duża; faktyczna zgodność archiwum,
niedegeneracja widoków i identyfikowalność instancji **nie zostały jeszcze sprawdzone**.
Wniosek o uczeniu, transferze i przewadze kosztowej pozostaje niedostępny bez eksperymentu.
Dokument tasku ma execution_authority=false. Nie implementowano generatora ani modelu
ASM01 i nie otwarto nowych danych. Ekonomiczne i naukowe bramki nie zostały osłabione.

## Koszty, awarie i integralność

| Obciążenie append-only | Sekundy |
|---|---:|
| NEXTAI-B-320-metadata-administration | 300 |
| NEXTAI-B-320-startup-doctor | 225 |
| NEXTAI-B-320-startup-lab-cli | 258 |
| NEXTAI-B-320-publisher-metadata | 55 |
| NEXTAI-B-320-storage-compression | 130 |
| NEXTAI-B-320-publisher-metadata-V2 | 59 |
| NEXTAI-B-320-maintenance-seal | 143 |
| NEXTAI-B-320-clone-conformance | 60 |
| NEXTAI-B-320-clone-conformance-V2 | 126 |
| NEXTAI-B-320-clone-conformance-V3 | 76 |
| NEXTAI-B-320-clone-lab-cli | 279 |
| NEXTAI-B-320-mirror-proof | 57 |

Łącznie **1768/1800 s** w cyklu, z fit badawczym **0 s**. B ma
**1/12** zużytych rejestracji i **7969.550240200/72000 s**
pełnego rozliczenia; pozostaje 64030.449759800 s, w tym chronione **7 rejestracji/47000 s**.
Niechroniony margines to 17030.449759800 s. A pozostaje11/17 i35649.98936010008 s;
wcześniejszy MUC03 pozostaje3 rejestracje/2655.336484700005 s. Nie przeniesiono niewydanego A do B.
Wszystkie rezerwacje pomocnicze są rozliczone. Maintenance, scoring=false, brak paid pending.

Zachowane porażki: pierwszy intake zatrzymała bramka dysku przed odczytem bajtów; drugi
zapisał surowe metadane, po czym serializer nie obsłużył brakującej długości HEAD.
Oryginalny helper i traceback zachowano; poprawka nie wymyśla długości. Pierwsza fikstura
clone-conformance miała błędny syntetyczny zakres ZIP; poprawiono ją. V2 zapisała JUnit
39/39 bez błędów, lecz proces przekroczył limit podczas końcowego sprzątania; timeout i126 s
pozostają porażką wykonania, nie PASS całego procesu. V3 z nowym lokalnym basetemp
zakończyła się poprawnie. Nie powtórzono żadnego płatnego EXP, seedów ani fitu źródła.
Pierwszy dowód mirroru zatrzymał się na swoim aktualnie powstającym pliku stderr, którego
klon jeszcze nie miał; porażka i57 s pozostają w ledgerze. Po rozliczeniu wykonania wszystkie
zamknięte pliki zostały skopiowane, a powtórna administracyjna kontrola bajtów przeszła.
Jej zmierzony czas drzewa procesu wyniósł 2.682072 s i jest
objęty wcześniej opłaconym300 s allowance na mirroring/administrację, bez dodatkowego
fitu ani nowej rejestracji. To porównanie zamkniętych plików, nie nowy test naukowy.

Próba rekurencyjnego usuwania zweryfikowanych kopii tymczasowych została zablokowana przez
automatyczną politykę i niczego nie usunęła. Bezpieczna alternatywa, przezroczysta kompresja
NTFS LZX, zachowała wszystkie ścieżki i bajty 26 wyników/kopii, odzyskując3 249 840 128 B.
Koszt przyszłego odczytu/dekompresji pozostaje w pełnej granicy pomiaru; historyczne
czasy i wyniki nie zostały zmienione. Nie zmieniano pagefile ani innych ustawień systemu.
Wolne miejsce na zakończeniu: **9150054400 B (8.522 GiB)**.
Po hipotetycznym capie320 MiB pozostałoby 8814510080 B;
bieżąca bramka≥10 GiB po operacji: **BLOCKED**.
Jest to migawka; przed przyszłym pobraniem/instalacją trzeba ponownie zmierzyć wolne miejsce.
RAR jest ograniczony strumieniem10 MiB i listą/extraction128 MiB; przekroczenie lub
niebezpieczna ścieżka zatrzyma intake przed fit; żaden większy download nie jest zatwierdzony.

## DECISION i NEXT DISCRIMINATING EXPERIMENT

**KEEP warunkową propozycję ASM01**, DISCARD processed-optdigits intake w tym protokole,
NIST pozostawiony jako nieprzetestowana alternatywa. Cały cel **ACTIVE**, bez promocji
architektury i bez twierdzenia, że naprawiono wszystkie możliwe problemy projektu.

Następny odrębny, ograniczony cykl: zamrozić kompletną recepturę ASM01 przed implementacją
i współrzędnymi (parser, normalizacja, DTW, score/margin, wszystkie siatki, metryki, progi,
capy i decyzja), testować minimalne publiczne fikstury w klonie, zweryfikować jedno legalne
ograniczone intake oraz natywne liczności, następnie freeze/preflight/readiness i dokładnie
jeden audytowany EXP z pięcioma świeżymi parami, trzema skalami i mocnymi kontrolami.
Nie zastępować brakującego/degenerowanego autora po odczycie. Przyszłe numeryczne HAR,
WT8–9, zewnętrzne modele/API, source replay i zmiany harmonogramu pozostają wykluczone.
Replikacje, świeże finały, drugi rzeczywisty test transferu i prototyp fact/source/update/UNKNOWN
pozostają niezrealizowanym zakresem programu, a nie osiągniętym wynikiem tego przygotowania.
