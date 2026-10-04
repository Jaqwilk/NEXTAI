# MUC03 — zakończenie autonomicznego programu

**Decyzja: INCONCLUSIVE dla porównania nowego mechanizmu z kompetentnym
transformerem.** Trzy zamrożone długości treningu (192, 768, 8192 kroków) nie
dały stabilnego referenta MUC spełniającego wszystkie bramki. Dodatni wpływ
treningu na ranking został potwierdzony w sparowanych badaniach; rozpoznawanie
braku odpowiedzi nadal zawodzi. Nie ma prototypu z potwierdzoną przewagą
inferencji ani podstaw do odrzucenia nieprzetestowanej rodziny delta-memory.

Program kończymy przez przewidzianą w prerejestracji gałąź „documented
inconclusive comparison with exact failed reference/integrity/power gate”.
Nie wyczerpano globalnego limitu. O końcu decyduje wcześniejszy limit trzech
receptur referencyjnych, który zapobiega niekończącemu się ratowaniu kontrolki.
Końcowa walidacja klonu jest PASS; tożsamości, stan kolejki i synchronizacja Git
są poświadczone oddzielnymi receipt, bez edycji zakończonych planów/wyników.

## OBSERVATION

### Przerejestrowane badania i historia

| Zakres | Niezmienny plan/wynik | Obserwacja i decyzja |
|---|---|---|
| Poprzedni etap random vs hard | EXP-20261004-0001, 4096 par, 192 kroki, 5 par seed/dane | Średni top1 10,96→23,11%, UNKNOWN 10,00→23,41%; oba jednoczesne CI obejmują zero. Known false abstention rośnie do 22,89%; jeden hard seed odrzuca 94,44% znanych. DISCARD tę recepturę jako gotową poprawę. |
| Ticket 1 obecnego programu | MUC03-DIAG-UNDERTRAINING-V1 | Rejestracja odrzucona przez historyczną fixture CLI przed planem, seedem lub fitem badawczym; ticket zużyty i zachowany. |
| Ticket 2 | [EXP-20261004-0002 plan](../plans/EXP-20261004-0002.json), [analiza](EXP-20261004-0002.md) | Hard 192 vs 768: train 77,32→95,75%, top1 22,74→70,15%; 5/5 dodatnich par i oba główne CI 97,5% wykluczają zero. KEEP diagnozę niedouczenia; 768 nie jest stabilnym referentem. |
| Ticket 3 | [EXP-20261004-0003 plan](../plans/EXP-20261004-0003.json), [analiza](EXP-20261004-0003.md) | Hard 768 vs 8192: train 98,54→99,87%, top1 84,52→91,93%; ponownie 5/5 dodatnich par i główne CI wykluczają zero. Nadal FAIL dla stałych bramek top1 i dense UNKNOWN. |

Wartości 768 z dwóch badań różnią się: użyto nowych seedów i nowych światów.
Nie wolno porównywać średnich między badaniami jak pojedynczej kontrolowanej
interwencji. Przyczynowy kontrast jest wewnątrz każdej sparowanej piątki.
Nie wybrano korzystnego seeda ani checkpointu. Pierwsze 768 strat w EXP-0003
są bitowo identyczne we wszystkich pięciu parach; inicjalizacja, 4096 par,
train/dev oraz grafy sond IID są hash-identyczne wewnątrz pary.

Ostatni etap został zamrożony przed implementacją w Git d6f0d0a, kontrakt
[MUC03-REFERENCE-CALIBRATION-V1](../plans/MUC03-REFERENCE-CALIBRATION-V1.json).
Źródło modelu Reader, sampler hard, loss, AdamW, próg 0,5, 6 warstw i szerokość
384 pozostają niezmienione. Jedynym czynnikiem badawczym są kroki 768/8192.
Wynik EXP-0003 jest complete: 11 workerów, 135 trial, 32 400 odpowiedzi E2E,
po 10 800 na każde ramię i kontrolę. Pięć jednostek to seed plus świeże dane;
32 400 odpowiedzi nie jest liczbą niezależnych replik.

### Ostatni kontrast i niepewność

| Metryka | 768 | 8192 | Różnica i przedział, pp |
|---|---:|---:|---|
| Accuracy par train, główna | 98,54% | 99,87% | +1,33; CI 97,5% [0,07; 2,59] |
| Dense latest-record top1, główna | 84,52% | 91,93% | +7,41; CI 97,5% [0,46; 14,35] |
| Dense UNKNOWN | 33,33% | 53,48% | +20,15; opisowy CI 95% [−17,62; 57,91] |
| End-to-end accuracy | 89,76% | 96,07% | +6,31; opisowy CI 95% [−2,42; 15,05] |
| Known false abstention | 0,52% | 0,00% | −0,52; wskaźnik ochronny |

Główne CI są dwustronnym paired Student-t, df=4, 97,5% każdy, z nominalną
Bonferroni familywise 95%. Założenia metody i n=5 ograniczają wniosek.
Opisowych CI nie używamy jako dodatkowych potwierdzonych odkryć. UNKNOWN
poprawia się w 3 parach, pogarsza w 1 i nie zmienia w 1; wszystkie pięć modeli
8192 pozostaje poniżej 90% dense UNKNOWN.

| Seed EXP-0003 | Train 8192 | Top1 dev 8192 | Dense UNKNOWN 8192 | E2E 8192 |
|---:|---:|---:|---:|---:|
| 72072428 | 100,00% | 95,19% | 57,04% | 93,70% |
| 1150792285 | 99,34% | 80,00% | 66,67% | 93,24% |
| 1781598374 | 100,00% | 91,48% | 16,67% | 97,78% |
| 535129614 | 100,00% | 97,41% | 66,67% | 98,06% |
| 1310994711 | 100,00% | 95,56% | 60,37% | 97,59% |

### Bramka referencyjna i rozdzielenie przyczyn

Długi wariant przechodzi train ≥99% w każdym seedzie, E2E średnio ≥90% i w
każdym ≥85%, ochronę znanych faktów oraz kontrolę symboliczną. Nie przechodzi
**top1 średnio ≥95%** (91,93%), **top1 każdego seeda ≥90%** (minimum 80%) ani
**dense UNKNOWN średnio ≥90%** (53,48%). Kryteria są identyczne z wcześniejszym
badaniem; nie obniżano ich po wyniku. Ani 768, ani 8192 nie jest wybranym
referentem. Wcześniejsze ekonomiczne bramki programu są jeszcze ostrzejsze
i dodatkowo wymagają matched-quality cost, replikacji, adverse oraz fresh final.

Niedouczenie wyjaśnia część porażki 192. Po 8192 train jest niemal idealny,
ale występują błędy rankingu i obecności klucza: absent-subject rejection
34,22%, absent-relation 72,74%. Top1 przy K=32/128/512 wynosi
100,00 / 95,33 / 80,44%. Namespace IID→D ma średni gap −0,07 pp, CI 95%
[−1,51; 1,36], poniżej zamrożonego warunku 10 pp. Brak sygnału tej konkretnej
zmiany namespace nie dowodzi transferu poza generator.

Post hoc obejrzano tylko już zapisane predykcje. Wśród 109 błędnych znanych
sond 8192 jest 23 z dokładnym remisem prawdopodobieństw, w tym 20 z obiema
wartościami równymi 1. Nie zachowano logits; nasycenie float32 i rzeczywisty
remis nie są rozdzielone. Nawet idealne naprawienie wszystkich 23 zwiększyłoby
top1 tylko do 93,63%, poniżej 95%; UNKNOWN przy progu 0,5 pozostałby bez zmian.
Nie uruchamiano inferencji od nowa ani nie ratowano wyniku zmianą tie-breakera.

### Pełna granica kosztów i klasyczna kontrola

| Ostatni etap, 5 jednostek | 768 | 8192 | Last-write graph |
|---|---:|---:|---:|
| Nadzorowany fit | 107,609 s | 959,265 s | 0 s |
| Pełny czas workerów | 526,344 s | 1376,562 s | 3,795 s |
| Dodatkowe sondy dense | 359,513 s | 358,556 s | nie dotyczą |
| Generowanie train/dev | 7,433 s | 7,283 s | zawarte w czasie workera |
| Zmierzony ingest z updates + warmup + 10 800 query | 41,041769 s | 40,431120 s | 0,177255 s |
| Pooled nearest-rank p95 query | 6,6707 ms | 6,6516 ms | 0,0037 ms |
| Maksymalny logiczny stan | 43 292 428 B | 43 292 428 B | 29 440 B |
| Accuracy E2E | 89,76% | 96,07% | 100,00% |

Łączny fit EXP-0003: **1066,874 s / 3500 s**, wszystkie role poniżej 350 s.
Pełni workerzy: 1906,701 s; każdy poniżej 2400 s. Peak RSS uczonego workera
1 158 774 784 B, peak CUDA reserved 698 351 616 B; obie granice zachowane.
Dłuższy fit kosztuje około 8,91 razy więcej. Operacje/FLOPs są estymowane:
fit 768 około 8,274e14, 8192 około 8,405e15 FLOPs; sondy każdego ramienia
około 3,535e15 FLOPs. Nie traktujemy tych estymat jako równego kosztu CPU/GPU.

Updates są podzbiorem ingest, zweryfikowanym multisetem próbek; ich czasu
nie dodajemy drugi raz. Ingest obejmuje parser, indeks i zastąpienia; query
obejmuje retrieval, kodowanie, matchera, synchronizację, decoding i pętlę.
new_session allocation nie jest oddzielnie zmierzona w sumie operacji; mieści
się w pełnym worker wall. Workerów nie używamy do matched-inference ratio,
bo mają różne dodatkowe workloady diagnostyczne. Nie zmierzono energii,
wartości pieniężnej ani skalowania na innym sprzęcie. Wall time nie jest
złożonością algorytmiczną.

Kontrola klasyczna dostaje ten sam raw UTF-8, publiczne timestampy i legalny
parser; nie otrzymuje ukrytych obiektów generatora ani odpowiedzi. Wszystkie
45 komórek ma 100% E2E i brak błędów parsera. Wspólne lokalne pomiary pokazują
znacznie lepszą jakość, mniejszy czas i stan niż sieć. To zamknięta syntetyczna
gramatyka, nie naturalny język ani ekonomiczny pojedynek z LLM.

Automatyczny front Pareto EXP-0003 pomija symbolic_last_write_graph_v2,
ponieważ jego osie obejmują sondy dense, które dla mapy są niezmierzone.
Nie interpretujemy go jako przewagi sieci nad mapą. Zachowano stare osie,
result i matematyczny front, a naprawa prezentacji jawnie wylicza niezmierzone
osie i kandydatów bez rankingu. [Post hoc audit wspólnych osi](../reviews/EXP-20261004-0003-pareto-coverage-audit.json)
pokazuje front zawierający samą mapę; jest opisowy i nie certyfikuje pełnej
ekonomii. Żaden niezmierzony dense wynik nie został zastąpiony zerem ani jedynką.

### Walidacja, awarie i budżet

W niezależnym Git klonie NEXTAI-VALIDATION-20261002 ukończono **1043/1043
końcowe testy**, 0 failures/errors/skips. Nowe testy prezentacji i kolejki sprawdzają brak
rankingu legalnej kontroli przy brakujących osiach i zachowanie osi/frontu.
Naprawa jest zamrożona przed kodem w
[MUC03-POSTRUN-REPORT-COVERAGE-V1](../plans/MUC03-POSTRUN-REPORT-COVERAGE-V1.json).
Model, dane, metryki, progi i zakończony result nie zmieniły się. Końcowy opis
kolejki jawnie zabrania następnego badania po terminalnym stanie; warunki
rejestracji i aktywnej kolejki zachowano. Naprawa została prerejestrowana
w MUC03-TERMINAL-QUEUE-DISCLOSURE-V1.json i sprawdzona w nowym teście.

Zachowano także wszystkie nieudane kontrole: pierwszy preseed ma 1 błąd fixture
kohorty (1040/1041 PASS), poprawiony preseed 1041/1041 PASS. Pierwszy postrun
ma 1 prawidłową blokadę należnego przeglądu po 12 wynikach (1040/1041 PASS).
Przegląd wykonano, zmieniono wyłącznie jego dwa liczniki stanu i timestamp;
nie osłabiono testu ani kadencji. Błąd inspektora nieistniejącego seed_events
oraz pomyłka nazwy komendy certyfikacji są utrwalone, bez treningu/rejestracji.
Pierwszy inspektor zamknięcia odczytał pole deadline z niewłaściwego poziomu
JSON; błąd zachowano i poprawiono odczyt z hash-bound study, bez nowego fitu.
Drugi błąd dotyczył wyłącznie wypisania zagnieżdżonego limitu fitu po zapisaniu
poprawnego proof; limit 3500 s potwierdzono z resources.fit_seconds_study_cap.
Ponowne sprawdzenie testów jest walidacją naprawy, nie retry eksperymentu.

Budżet programu: **3/20 rejestracji** (1 odrzucona + 2 zakończone badania); **1216.336485 s fitu badawczego** + **1439 s konserwatywnej opłaty testów** = **2655.336485 s / 72 000 s**. Pozostaje 69344.663515 s, lecz trzy-recepturowy warunek końca jest wiążący. Pozostałe etapy mają 0 rejestracji; limit globalny nie został wyczerpany.

Każdy testowy czas wall jest konserwatywnie opłacony jako górna granica fitu
fixture, z rezerwacją przed uruchomieniem; także failed runs. Dawne budżety
PC-01, WT i hard-v-random pozostają oddzielnie zużyte. Nie ma pending plan,
rezerwacji fitu, aktywnego workera ani wykorzystania niezużytego ticketu.

Przed zmianą chronionych plików po zakończeniu zachowano **996 plików źródła**
(4 121 565 B) i **89 plików runtime** (94 110 726 B) z raw hashami. Dzienniki
fsync zawierają 6080 propozycji: 6075 akceptowanych, 5 odrzuconych; 2 różne
odrzucone adresy świata, najwyższa propozycja 1. Były to prerejestrowane
odrzucenia niewykonalnej struktury pytań, przed predykcjami, nie wybieranie
korzystnych danych ani zastępowanie training seedów. Każdy seed propozycji
sprawdzono ze świeżym tagiem; wygenerowano tylko T/D. **Nie było fresh final,
WT 8–9, API/modeli zewnętrznych, nowej architektury, instalacji, pobierania ani
zmiany harmonogramu.** Stan: 110 ukończonych wyników, cycle 303.

## INTERPRETATION

Projekt ma sens jako rygorystyczne laboratorium odrzucające nieskuteczne
pomysły i naprawiające własne pomiary. Zbudowane wcześniej PC-01 rzeczywiście
wykazało kontrolny efekt gradientowego uczenia, a WT powtórzyło lokalny efekt
rekurencji równoważny klasycznemu ARX. MUC teraz rozdziela dopasowanie łatwych
par od rankingu i kalibracji braku faktów. To postęp w wiedzy i aparaturze.
Nie jest to dotąd postęp do następcy LLM ani dowód przewagi kosztowej.

Obecna publiczna gramatyka jest bardzo dogodna dla dokładnej mapy. Kolejny
kosztowny matcher bez jasno rozdzielającego pytania nie ma na tych danych
uzasadnionej ekonomii. Zamknięcie nieskutecznej receptury jest zgodne z celem
projektu, który stawia dowód ponad ochroną wybranej architektury.

[Przegląd 12 najnowszych wyników](../reviews/MUC03-REFERENCE-PORTFOLIO-CYCLE-303-V1.md)
wraz z zachowaną syntezą pierwszych 98 wpisów opisuje postęp całego portfela.
Nie łączymy różnych metryk w pozorną meta-analizę ani crashów z falsyfikacją.

## CONFIDENCE

Wysoka pewność: wykonanie, parowanie, raw historia oraz nieprzejście jawnych
bramek. Umiarkowana, warunkowa: lokalny dodatni efekt zwiększenia kroków na
ranking dla tego generatora. Niska: przyszły efekt UNKNOWN i wynik nowego
mechanizmu, którego nie implementowano. Świeży jawny train/dev to development,
nie niezależnie niewidoczny holdout. Niewykonany final pozostaje niewykonany.

## ALTERNATIVE EXPLANATIONS

Dopasowanie train może nie odpowiadać many-record rankingowi; próg 0,5 może
być niekalibrowany dla nieobecnych podmiotów; score może używać skrótów,
a float32 może nasycać prawdopodobieństwa. Tych przyczyn nie rozdzieliliśmy
odrębną interwencją. Namespace wyjaśnienie osłabia tylko konkretny probe.
Kolejny loss/sampler/threshold jest inną hipotezą i wymaga prospektywnego
kontraktu; nie może być po wyniku czwartą recepturą w tym programie.

## DECISION

**KEEP** odtwarzalną aparaturę i potwierdzoną lokalną diagnozę niedouczenia.
**DISCARD** przetestowane receptury jako stabilny referent MUC.
**INCONCLUSIVE**: ekonomiczne porównanie mechanizmu i rodzina delta-memory.
Brak promocji, transferu, scaling law lub nowej zasady computationalnej.
To zgodna z umową gałąź zakończenia programu z dokładnym nieprzejściem bramki,
a nie wykonanie całego warunkowego zakresu badań.

| Wymaganie programu | Stan |
|---|---|
| Diagnoza po EXP-0001 i prerejestracja progów | Wykonane; dwa nowe pięcio-parowe badania i sondy fit/ranking/rejection/namespace |
| Stabilny kompetentny transformer MUC | Nie osiągnięty; trzecia i ostatnia receptura FAIL top1/UNKNOWN |
| Wybór/implementacja nowego mechanizmu | **Niewykonane**, nieprzejście warunku wejścia |
| Source-identical mechanizm i ablacje | **Niewykonane** |
| Dopasowana jakość, trzy skale kosztu i adverse generalization | **Niewykonane**; dostępne K/D diagnostyki nie zastępują tego porównania |
| Zamrożona receptura i świeży final z replikacją | **Niewykonane**; final nie wygenerowany ani obejrzany |
| Odtwarzalne źródła, koszty, niepewność, historia i testy klonu | Wykonane i poświadczone receipt |
| Potwierdzona przewaga nad referentem/klasyką | **Nie wykazana** |
| Dozwolony wynik końcowy: udokumentowana ocena INCONCLUSIVE | Osiągnięty po końcowym audycie; exact failed reference gate jawny |

## NEXT DISCRIMINATING EXPERIMENT

Żaden dalszy run w zamkniętym MUC03. Ewentualny odrębny program musiałby
najpierw zarejestrować jedno rozdzielenie rankingu wielu kluczy i kalibracji
absent-subject, z tym samym zamrożonym kontrolnym źródłem i nowymi train/dev;
wybór metody, progów i budżetu musi wyprzedzać wynik. Dopiero kompetencja
umożliwia mechanizm/ablacje/matched-quality/fresh-final. Nie jest to obecnie
plan wykonania, rejestracja ani autoryzacja nowego eksperymentu.
