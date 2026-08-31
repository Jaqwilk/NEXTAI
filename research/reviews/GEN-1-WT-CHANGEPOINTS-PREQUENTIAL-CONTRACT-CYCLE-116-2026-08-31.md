# GEN-1 — WT changepoints prequential contract gate, cykl 116

Zakres: jeden no-scoring design gate na zamrożonym lokalnym manifeście. Nie utworzono
benchmarku, evaluatora, hipotezy, planu, seeda, kandydata ani wyniku i nie wykonano scoringu.
Kontrakt zapisano w `research/checks/wt_changepoints_prequential_contract_gate_v1.json`.

## Obserwacje

Prosty whole-file split został ustalony przed sprawdzeniem pokrycia: train seed 0–5,
development 6–7, test 8–9. Po odrzuceniu pierwszego zdarzenia bez historii daje odpowiednio
54, 18 i 18 epizodów przejścia. Train obejmuje wszystkie 12 uporządkowanych przejść między
czterema różnymi poziomami. Development i test nie zawierają żadnego przejścia niewidzianego
w train. Zakres długości testowych 112–294 mieści się w train 100–297. Naturalny transition
OOD oraz naturalny response-length OOD zatem nie istnieją.

Mechaniczna reguła uczona wyłącznie na train wskazuje dokładnie jeden kanał sterowania:
jedyną liczbową kolumnę zmieniającą się przy wszystkich 54 niepoczątkowych markerach i nigdy
między markerami. Dziesięć kanałów outcomes wyznacza reguła niezerowej zmienności wewnątrz
segmentu; 21 stałych lub protokolarnych kanałów odpada bez użycia ich znaczenia. Kandydat
otrzyma wyłącznie anonimowe tensory, bez nazw, seeda, pliku, markera i czasu absolutnego.

Trzy zamrożone skale historii to K=18/36/54 epizodów, w porządku event-index-first,
seed-second. Każdy prefix obejmuje wszystkie sześć plików train i cztery poziomy; K=36 i 54
obejmują wszystkie przejścia. Fit-depth 32 oraz horizon 16/32/96 są wykonalne dla każdego
epizodu. Horizon 96 jest jednak sztucznie zdefiniowaną ekstrapolacją głębokości evaluatora,
nie naturalnie niewidzianym mechanizmem.

## Zamrożona prospective boundary

Przed predykcją learner widzi ostatnie 32 anonimowe wektory outcomes, bieżącą anonimową
wartość sterowania i żądany horyzont. Musi atomowo zwrócić cały tensor predykcji przed
ujawnieniem targetu. Dopiero potem wolno naliczyć lokalny update; globalny refit jest hard
failure. Niedozwolone są bieżące/future outcomes, marker, czas, plik/seed, native names,
przyszły harmonogram sterowania i dostęp kandydata do systemu plików.

Jakość obejmuje train-normalized NRMSE overall, worst-file, worst-transition/level i osobno
horyzonty 16/32/96. Raportowane są stabilność pełnych rolloutów, lokalność update oraz pełny
koszt od pozyskania danych przez partition, fit, query i update po pamięć, bajty i workload
R1/R4/R16. Obowiązkowe kontrolki obejmują persistence, pooled mean, dokładny public-control
level bank, LMS/ARX, RLS/Kalman, transition bank, bounded replay oraz ridge/FIR.

## Interpretacja i niepewność

Kontrakt jest wykonalny bez ręcznej ontologii i ma poprawną granicę predict–reveal–update.
Nie spełnia jednak pierwotnego wymagania naturalnego OOD. Nie wiadomo też jeszcze, czy jawna
wartość sterowania nie pozwoli prostemu control-level bank albo RLS rozwiązać zadania niemal
trywialnie. Sprawdzanie tego w tym cyklu wymagałoby implementacji i development run, których
zakres design gate jawnie zabrania.

Confidence `0.99` dla audytu pokrycia i wykonalności boundary. Confidence `0.75`, że depth-96
może być użytecznym lokalnym screeningiem; największa niepewność to nietrywialność względem
klasycznych kontrolek. To nie jest evidence learnera ani podstawa promotion.

## Decyzja

`contract_feasible_pending_dev_baseline_gate`. Nie aktywować benchmarku i nie tworzyć
chronionego evaluatora. Nie tworzyć HYP-0028 ani EXP-20260831-0006.

## Następny rozstrzygający krok

Dokładnie jeden osobny no-scoring development-only baseline feasibility service. Ma użyć
najmniejszego lokalnego preflightu, uruchomić obowiązkowe persistence, public-control level
bank oraz adaptacyjną kontrolkę liniową wyłącznie na seedach 0–7, a przed wynikiem zamrozić
noise/minimum-meaningful-effect z development. Test seedów 8–9 pozostaje niewidoczny.
Jeżeli prosta kontrolka saturuje jakość albo dominuje kosztowo, zapisać
`reject_before_benchmark`. Tylko pełny PASS może zezwolić w jeszcze późniejszym cyklu na
chronioną implementację benchmarku; nie zezwala sam w sobie na scoring.
