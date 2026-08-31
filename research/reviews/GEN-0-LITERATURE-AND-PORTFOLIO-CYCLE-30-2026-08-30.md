# GEN-0 — przegląd literatury i portfolio, cykl 30

Zakres: obowiązkowy wake review-only po 29 ukończonych eksperymentach. Obejmuje EXP-0025–0029 od poprzedniej refleksji w cyklu 24. Nie utworzono planu, nie zmieniono benchmarku, nie napisano kodu kandydata i nie wykonano scoringu. Dodano osiem źródeł pierwotnych `SRC-0070–SRC-0077`.

## 1. Czego obiektywnie się nauczyliśmy?

- Pięć różnych learned routes osiągnęło dokładność na swoich małych zamkniętych kohortach, ale żadna nie uzyskała przewagi nad kontrolą klasyczną o tej samej zdolności.
- EXP-0025: soft unification odzyskało opaque aliases bez false reuse, lecz exact constraints były tańsze w każdej komórce i miały lepszą skalę K.
- EXP-0026: contrastive motif composer był exact na held-out kompozycjach, ale fixed trigram miał `10.18x` niższy workload, a exact suffix `3.53x` mniej query ops i `3.61x` mniej workload.
- EXP-0027: event predictive state był exact, lecz screened switching AR zachował tę samą zdolność; learned route zużył `19.48%` więcej query ops, `5.56%` więcej update ops, `29.63%` więcej stanu i `1.38%` więcej workload.
- EXP-0028: polychronous binder był exact, lecz timed automaton dorównał mu; learned route zużył `14.55%` więcej query ops, `39.34%` więcej update ops, `35.29%` więcej stanu i `12.54%` więcej workload.
- EXP-0029: learned acquisition i certified tree osiągnęły dolną granicę `D*log2(K)` probes oraz pełną poprawność, ale learned route miał odpowiednio `8.00%`, `41.67%`, `62.50%`, `19.21%`, `60.19%` i `35.08%` więcej query, mean fit, policy build, max state, update i workload.
- Powtarzalny wynik dotyczy granicy systemu: po zdobyciu dobrego indeksu/stanu lokalne query może nie zależeć od K, ale fit, skan surowego wejścia, konstrukcja reprezentacji, stan lub aktualizacja nadal rosną. Nie jest to dowód niemożliwości dla open-world learning.

## 2. Które założenia zostały sfalsyfikowane?

- Learned parametrization nie jest sama w sobie nową zasadą, jeżeli po treningu implementuje dokładnie constraints, suffix index, AR state, timed automaton albo decision tree.
- Niski fitted K exponent nie oznacza lepszej asymptotyki, jeśli wynika z dużej stałej dla małego K i większego absolutnego przyrostu.
- Exact i safe reuse na ręcznie identyfikowalnym generatorze nie dowodzi autonomicznego uczenia reprezentacji.
- Selektivne obserwowanie jest wartościową zasadą, ale learned acquisition nie ma domyślnej przewagi nad klasycznym drzewem lub information gain.
- Seria pięciu potwierdzeń nie uzasadnia confidence `0.89` dla uniwersalnie brzmiącej HYP-0012: wszystkie testy były quick, single-seed, małe, syntetyczne i skonstruowane tak, by ujawniać ukryty koszt.

## 3. Które wyniki się zreplikowały?

- W EXP-0025–0029 pięć razy powtórzył się null: learned mechanism był poprawny, ale odtwarzał tańszy mechanizm klasyczny przy pełnym rozliczeniu.
- W EXP-0026–0029 powtórzyła się lokalna praca query niezależna lub słabo zależna od K po opłaceniu reprezentacji/routingu.
- W całym portfolio powtarza się korzyść z kompilacji, indeksowania, zdarzeń i selektywnej obserwacji. Replikuje się zasada implementacyjna, nie learned successor architecture.
- Nie zreplikowano dodatniej learned przewagi między niezależnymi rodzinami, na wielu seedach ani w open-world/OOD środowisku.

## 4. Czy portfolio utknęło w jednej rodzinie?

Tak, mimo zmiennych etykiet. EXP-0025–0029 są pięcioma wariantami pytania „czy learned routing ukrywa koszt?”, więc HYP-0012 stała się generatorem potwierdzeń zamiast falsyfikowalnym projektem architektonicznym. Dalsze strojenie tej serii jest zabronione. HYP-0012 pozostaje dyscypliną pomiarową i kontrolą null, ale nie wybiera następnego eksperymentu.

## 5. Czy optymalizujemy implementację zamiast zasady?

Ryzyko jest wysokie. Każda ostatnia kohorta dodała inną powierzchnię wejścia, lecz rdzeń rozstrzygnięcia był ten sam: learned candidate rekonstruował znany algorytm. Następny test musi zmienić źródło stanu, a nie optymalizator: nie dostaje latent IDs, codebook, segmentacji, generatora ani prawdziwych stanów. Ma odkryć behawioralnie wystarczającą reprezentację z historii.

## 6. Jaki wynik najbardziej zmieniłby przekonania?

Learned predictive representation z surowych action-observation histories musiałaby jednocześnie:

- odkryć zwarty stan bez state labels i privileged model;
- zachować prediction i planning na nowych kompozycjach działań oraz po permutacji obserwacji;
- bezpiecznie rozróżniać prawie równoważne historie;
- mieć niższy skumulowany pełny koszt niż CSSR, spectral PSR i dokładna empiryczna partycja po wliczeniu treningu, statystyk suffixów, SVD/negatives, planowania, stanu i aktualizacji;
- powtórzyć wynik na wielu seedach i po lokalnej zmianie dynamiki bez zapomnienia niezmienionej części.

Taki wynik byłby dowodem, że amortyzowana reprezentacja daje coś więcej niż ręcznie dostarczony indeks. Null pokaże, że nowa warstwa znów rekonstruuje klasyczny predictive quotient.

## 7. Która wcześniejsza praca zawiera pozorną nowość?

| Pozorna nowość | Prior art | Konsekwencja testowa |
|---|---|---|
| Szybka amortyzowana inferencja | VAE inference gap (`SRC-0070`) | Oddziel training, approximation i amortization gap. |
| Minimalna informacja istotna dla decyzji | Information bottleneck (`SRC-0071`) | Porównaj kompresję i policz iteracyjne dopasowanie. |
| Learned algorytm adaptacji w recurrent state | Meta-RL (`SRC-0072`) | Policz outer training i ograniczenie do task family. |
| Learned kupowanie obserwacji | Costly features RL (`SRC-0073`) | Użyj niehandcrafted features i silnych klasycznych kontroli. |
| Odkrycie minimalnego stanu predykcyjnego | CSSR (`SRC-0074`) | CSSR jest obowiązkowym non-neural baseline. |
| Stan z action-observation histories i planning | Spectral PSR (`SRC-0075`, wcześniej `SRC-0060`) | Learned state musi pokonać statystycznie spójny spectral control. |
| Behawioralna równoważność stanów | Bisimulation metrics (`SRC-0076`) | Mierz decision loss, nie tylko embedding similarity. |
| Self-supervised future-predictive latent | CPC (`SRC-0077`) | Policz encoder, context model, negatives i raw pass. |

Literatura osłabia absolutne brzmienie HYP-0012, ale nie usuwa obowiązku pełnego accounting. Pokazuje dokładnie, jakie amortyzowane mechanizmy trzeba uczciwie dopuścić do testu.

## 8. Który następny test ma największą oczekiwaną informację?

Reaktywować HYP-0008 jednym `action_conditioned_predictive_equivalence_v1` quick. Jest to radykalny pivot od HYP-0012 i spełnia wcześniejszy warunek wyjścia poza binary-DAG toy.

### Minimalna kohorta

- Dane: surowe epizody z aliased probabilistic transducers; wejście zawiera tylko actions, observations i rewards. Brak state IDs, modelu przejść, codebook, segmentacji i latent oracle podczas fit.
- OOD: nowe kompozycje działań, permutacje symboli obserwacji, dłuższe historie i confusable irrelevant-history K. Near cases różnią się małym, decyzjotwórczym przyszłym prawdopodobieństwem.
- Zadania: wielokrokowa predykcja action-conditioned futures, wybór działania i krótki planning; potem lokalna zmiana jednego mechanizmu oraz test retencji pozostałych.
- Kontrole: n-gram/context tree, CSSR-style causal states, spectral PSR, bisimulation/empirical predictive partition, small recurrent encoder, CPC encoder, information-bottleneck encoder i latent-state oracle.
- Accounting: raw pass, suffix/future statistics, tests statystyczne, matrix/SVD, negatives, fit, routing, rollout/planning, stored state, memory traffic, update i pełny repeated-use workload.
- Sygnał dodatni: exact lub preregistered calibrated-safe decision accuracy w każdym seedzie, OOD bez false merges, zwarty stan i non-dominated full workload względem CSSR/spectral/exact controls. Quick nie może promować.
- Null/negative: learned state tylko odtwarza classical quotient, przewaga znika po pełnym fit/state accounting, albo OOD łączy decision-distinct histories. Wtedy HYP-0008 wraca do dormant bez serii poprawek.

Kontrakt implementacyjny: jeden mały współdzielony rdzeń, jeden benchmark i cienkie adaptery; najpierw reuse istniejącego harnessu. Bez frameworka, zewnętrznego modelu/API i bez nowej zależności, chyba że brak zależności uniemożliwia uczciwy spectral/recurrent control.

## Decyzja portfelowa

- HYP-0012 pozostaje `testing`, ale confidence zostaje skalibrowane z `0.89` do `0.78`. To korekta nadmiernej pewności i selection bias, nie nowe evidence przeciw z eksperymentu. Zamrozić kolejne kohorty HYP-0012 do czasu niezależnego learned wyniku.
- HYP-0008 przechodzi z `dormant` do `testing` przy niezmienionym confidence `0.30`. Zmiana oznacza wybrany test, nie wzrost wiary.
- Żadna hipoteza nie przechodzi do `promising` ani `promoted`. W cyklu 30 nie ma eksperymentu, wyniku ani punktu w leaderboardzie.
