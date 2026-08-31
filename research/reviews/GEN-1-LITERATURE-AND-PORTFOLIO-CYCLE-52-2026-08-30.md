# GEN-1 — połączony przegląd literatury i portfolio, cykl 52

Zakres: obowiązkowy review-only wake po 47 ukończonych eksperymentach, uruchomiony jednocześnie przez kadencję reflection (12 wyników od completed=35) i literature review (6 wyników od completed=41). Nie utworzono planu eksperymentu, nie zmieniono benchmarku, evaluatora ani kodu kandydata, nie wylosowano seeda i nie uruchomiono runnera. Dodano dziewięć źródeł pierwotnych `SRC-0116`–`SRC-0124`.

## 1. Czego obiektywnie się nauczyliśmy?

- Sześć wyników powstałych od poprzedniego przeglądu to EXP-0046, 0047, 0048, 0050, 0051 i 0052. EXP-0046 i EXP-0047 są terminalnie naukowo nieważne z powodu `invalid_control_semantics`; pozostają widoczną historią diagnostyczną, lecz są wykluczone z evidence, Pareto, confidence, falsyfikacji i replikacji. Naprawa infrastruktury wprowadziła semantyczny rejestr baseline'ów i prawdziwe PPM-D/CTW przed kolejnym scoringiem.
- EXP-0048 był ważnym testem jednego współdzielonego width-32 recurrent predictive state. Shared uzyskał `0.015625` transferu, minimum-family `0.0` i był gorszy od source-identical independent o `0.057292` overall. Contextual Chow–Liu był exact i jedynym accuracy-gated implementowalnym punktem Pareto.
- EXP-0050 zmienił readout tej samej reprezentacji na capacity-48 predictive dictionary. Shared osiągnął `0.046875`, minimum-family `0.0` i ponownie przegrał z independent (`-0.015625`). To odrzuciło wyjaśnienie, że sam liniowy readout odpowiadał za EXP-0048.
- EXP-0051 przetestował odrębny cap-64 relation-fragment graph. Shared uległ awarii przed próbą z powodu niepełnej emisji komponentów, ale independent ukończył z `0.208333` i minimum-family `0.0`. Awaria została zachowana jako failure implementacji, nie wynik zerowy.
- EXP-0052 prerejestrował wyłącznie totalny fallback i ukończył graph learner bez zmiany evaluatora. Shared osiągnął `0.223958`, minimum-family `0.0`; independent `0.197917`, minimum-family `0.0`. Pooled advantage wyniósł tylko `+0.026042` overall i `0` na minimum-family, wobec wymaganych `+0.05` na obu osiach. Contextual Chow–Liu osiągnął `0.989583 / 0.958333` i pozostał jedynym accuracy-gated implementowalnym punktem Pareto.
- Trzy naukowo ważne współdzielone implementacje na frozen cross-family boundary — recurrent linear, recurrent dictionary i explicit relation fragments — uzyskały odpowiednio `0.015625`, `0.046875` i `0.223958`, każda z minimum-family `0.0`. To replikuje brak użytecznego transferu dla tych implementacji, ale nie jest dowodem niemożliwości shared representation.
- HYP-0017 nadal nie ma żadnego ważnego wyniku. EXP-0047 nie może być evidence, a jego późniejsza naprawa semantyczna stworzyła `heldout_parallel_masked_infilling_v2` z prawdziwymi PPM-D i CTW, lecz użytkownik skierował wtedy badania do cross-family transfer przed poprawionym rerunem.
- Portfolio ma 20 hipotez: 18 dormant, HYP-0012 `testing` jako reguła accounting i HYP-0017 `proposed` jako nieprzetestowana zmiana factorization. Nie ma learned architecture, która przeszła multi-seed, adversarial/OOD i pełny Pareto w więcej niż jednej rodzinie.

## 2. Które założenia zostały sfalsyfikowane?

- Jedna lossless składnia i jedna pula parametrów nie stanowią dowodu wspólnej reprezentacji. Mogą jedynie zmusić niekompatybilne statystyki do konfliktu.
- Naprawa readoutu nie wystarczyła recurrent state: zarówno liniowy head, jak i dictionary composition zawiodły, a pooling miał ujemny znak.
- Jawne structural fragments i multi-fragment trace nie wystarczają do systematycznego transferu. Zachowanie wymaganej kompozycyjnej semantyki na małym fixture nie przewidziało zdolności w czterech światach.
- Sama nazwa baseline'u nie dowodzi semantyki algorytmu. Dwa nieważne wyniki wykazały, że source audit musi być uzupełniony discriminating conformance tests oraz hashami implementacji i testów.
- Zakaz jawnego family label nie usuwa family identity. Audyt fixed training data dla K=32, D=6 pokazał cztery niepokrywające się profile supportu. Wektor `długość + liczności markerów -1..-7` sklasyfikował rodzinę `12/12` przy leave-one-training-seed-out; profile były identyczne dla wszystkich trzech seedów. Potencjalny learner może więc odkryć ukryty router z samego kształtu.
- Obecny v4 nie ustanawia, że rodziny współdzielą latentny mechanizm. Generatory są niezależnie zbudowanymi probabilistic, predictive, local i program tasks. Wymóg `shared > independent` zakłada pozytywny transfer, którego data-generating process nie gwarantuje ani nie czyni identyfikowalnym.

## 3. Które wyniki się zreplikowały?

- Na trzech ważnych shared mechanisms powtórzyły się minimum-family `0.0`, duża luka do specialist capability i brak wymaganego pooled advantage.
- W każdym ważnym cross-family wyniku native contextual Chow–Liu osiągał około `0.99–1.0` overall i był jedynym accuracy-gated implementowalnym punktem Pareto. Światy są rozwiązywalne, ale przez rodzinowo właściwe statystyki.
- W dwóch kolejnych readoutach tej samej recurrent representation pooling był gorszy od independent. Relation fragments dały mały dodatni overall effect, lecz dokładnie zerowy effect na najgorszej rodzinie.
- Po raz kolejny tania query slope bez capability nie ma wartości sukcesora. Shared graph miał depth-compute slope `0.05108`, ale local accuracy `0.0` i program accuracy `0.041667`.
- Zreplikowała się także reguła procesowa: mechaniczna integralność hashy nie zastępuje semantycznego testu kontrolki. Naprawa EXP-0047 jest teraz trwałą bramką dla przyszłych kohort.

## 4. Czy portfolio utknęło w jednej rodzinie?

Tak, w ostatnich ważnych wynikach. Powierzchniowo zmieniano recurrent state, retrieval dictionary i relation graph, ale wszystkie trzy próby optymalizowały ten sam czterorodzinny evaluator oraz tę samą tezę, że pooling niepowiązanych rodzin sam ujawni wspólną reprezentację. EXP-0052 zamyka tę serię.

Portfolio jako całość jest szersze — zawiera active execution, program libraries, probabilistic circuits, online updates, real compression i masked infilling — lecz priorytet ostatnich wake'ów zawęził się do representation interface. Najwyższą informację daje teraz powrót do nieprzetestowanej osi output factorization HYP-0017, a nie v5 cross-family learner.

Przyszły powrót do shared representation wymaga innego data-generating contract: te same evaluator-hidden mechanizmy muszą występować w wielu treningowych kombinacjach, a test musi trzymać niewidziane kombinacje, nie całkiem niepowiązane rodziny. Support shapes muszą być zbalansowane tak, by family/routing identity nie była prostym substytutem transferu.

## 5. Czy optymalizujemy implementacje zamiast zasad?

Tak, gdyby kontynuować v3/v4. Zmiana width, capacity, cap grouping, distance, learned similarity, output head albo training seed byłaby teraz tuningiem po trzech zdecydowanych nullach. HYP-0019 i HYP-0020 pozostają dormant.

Literatura wskazuje trzy odrębne poziomy przyszłego testu:

| Poziom | Kontrolki / prior art | Co naprawdę trzeba rozstrzygnąć |
|---|---|---|
| Reprezentacja zbioru obserwacji | Neural Statistician (`SRC-0116`), CNP (`SRC-0117`), Deep Sets (`SRC-0123`), Set Transformer (`SRC-0124`) | Czy unordered support można skompresować bez utraty statystyki potrzebnej query? |
| Rekombinacja modułów | Modular meta-learning (`SRC-0118`) | Czy learner odkrywa wielokrotnie użyte mechanizmy i składa je w niewidzianej kombinacji po policzeniu search/fit? |
| Identyfikowalność | IMA (`SRC-0119`), compositional first principles (`SRC-0121`), provable object-centric generalization (`SRC-0122`) | Jakie zmiany środowiska i support coverage pozwalają odróżnić prawdziwe moduły od arbitralnej reparametryzacji? |

Slot Attention (`SRC-0120`) jest ważnym object-centric precedensem, ale nie wolno przenieść jego object bias do symbolicznego benchmarku jako darmowej ontologii. Nowa nazwa „slot” nie rozwiązuje identyfikowalności.

## 6. Jaki wynik najbardziej zmieniłby przekonania?

Najbliższy wynik o najwyższej wartości to ważny test HYP-0017 po semantycznej naprawie. Przekonania zmieniłby iterative masked learner, który na całych niewidzianych plikach:

- ma niższy mean i worst-span conditional bits/byte niż prawdziwe PPM-D, CTW, dense AR, exact bidirectional Markov i parallel BP;
- ściśle pokonuje source-identical forced-one-pass learner;
- utrzymuje critical path zależny od `R=1/4/6`, a nie span length `8/32/128`;
- nie jest implementowalnie Pareto-dominated po policzeniu wszystkich position-round probabilities, acquisition, fit, confidence selection, updates, state, bytes i R16 work;
- przechodzi byte relabeling i whole-file holdout bez path/target leakage.

Negatywny wynik również jest wartościowy: jeśli prawdziwe CTW/bidirectional inference albo one-pass learner dorównają jakości taniej, parallel refinement staje się dormant bez dalszego tuningu.

Dla późniejszego shared-mechanism kierunku przekonania zmieniłby dopiero learner wygrywający na held-out kombinacjach evaluator-hidden modules, gdy monolithic set encoder, independent fits, exact MDL module library i oracle-structure lower bound są jawnie porównane. Obecny v4 nie może dostarczyć takiego dowodu.

## 7. Która wcześniejsza praca zawiera pozorną nowość?

- Dataset-level representation nie jest nowe: Neural Statistician i CNP uczą reprezentacji support set/dataset.
- Permutation-invariant pooling nie jest nowe: Deep Sets charakteryzuje tę klasę, a Set Transformer dodaje interactions i inducing points.
- Uczenie i rekombinacja modułów nie są nowe: modular meta-learning robi to przez jawnie płatny structure search.
- Object-centric slots nie są nowe: Slot Attention uczy exchangeable slots przez iterative competitive attention.
- „Niezależne mechanizmy” nie są automatycznie identyfikowalne: IMA wymaga dodatkowych założeń strukturalnych, a prace Wiedemera i współautorów formalizują support/decoder consistency potrzebne do compositional generalization.
- Parallel masked refinement również nie jest nowe: D3PM, MaskGIT i Levenshtein Transformer (`SRC-0110`–`SRC-0112`) pozostają bezpośrednim prior art. HYP-0017 testuje ekonomię tej factorization, nie autorstwo mechanizmu.

## 8. Który następny test ma największą oczekiwaną informację?

Najpierw jeden service-only wake, ponieważ aktywny protected manifest jest v4. Nie wolno w nim tworzyć EXP-0053 ani seeda i nie wolno scoringu.

1. Reaktywować istniejący `heldout_parallel_masked_infilling_v2` bez zmiany jego corpus split, mask geometry, spans, rounds, query boundary, metrics, state budget lub success criteria.
2. Zachować PPM-D order 5, full exclusion, frozen-count inference oraz generalized 256-ary CTW depth 2 z KT(1/2) i exact `0.5 local / 0.5 child-product` recursion. Runner ma wykonać zarejestrowane semantic nodes przed seedem; first-order impostor musi nadal failować.
3. Zweryfikować wszystkie candidate/test hashes, odtworzyć nowy full-harness manifest wymagany przez obecny protocol-v2 i jawnie zapisać, że zmiana digestu wynika z aktywacji kohorty oraz późniejszej historii harnessu, nie ze strojenia masked evaluator.
4. Uruchomić pełne testy, semantic baseline tests, corpus verification, integrity i doctor. Jeśli którakolwiek semantyka v2 nie może być odtworzona dokładnie, pozostawić maintenance i nie planować wyniku.

Po PASS dopiero następny wake może prerejestrować `EXP-20260830-0053` quick na v2: K=`8/32`, D=`1/4/6`, Q=`8`, spans=`8/32/128`, jeden runner-random seed. Kandydaci: `iterative_masked_learner`, `one_pass_masked_learner`, `uniform_masked_byte`, `empirical_unigram_masked_byte`, `left_to_right_ppm_masked_byte`, `context_tree_weighting_masked_byte`, `dense_autoregressive_masked_byte`, `bidirectional_markov_masked_byte`, `parallel_markov_bp_masked_byte`, `oracle_conditional_masked_byte`. Primary axes: mean/worst-span conditional bits per byte, exact-span accuracy, critical path, total/R16 work, state i bytes touched. Quick może tylko odrzucić HYP-0017 albo autoryzować nowy-corpus three-seed screen; nigdy promować.

## Decyzja portfolio

- HYP-0017 pozostaje `proposed` z confidence `0.16`; brak ważnego evidence. Otrzymuje najwyższy priorytet, bo naprawiony test bada nieprzetestowaną factorization i jest tańszy informacyjnie niż budowa nowego learnera.
- HYP-0012 pozostaje `testing` na `0.80`. EXP-0048, 0050, częściowy 0051 i 0052 są zgodnymi lokalnymi nullami, ale dwa invalid results oraz wykryta family-shape separability zabraniają podnoszenia confidence jako uniwersalnego lower bound.
- HYP-0019 i HYP-0020 pozostają dormant. Nie tworzyć v5 ani nie stroić recurrence/dictionary/fragments.
- Nie tworzyć jeszcze nowej hipotezy object-centric/modular. Najpierw przyszły design gate musi dowieść mechanism sharing, support coverage, held-out recombination oraz braku shape-based family routing. Bez tego powstałaby kolejna nazwa dla HYP-0010 albo benchmark przenoszący ontologię do generatora.
