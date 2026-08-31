# Katalog przestrzeni poszukiwań

## Jak czytać katalog

To nie jest backlog funkcji do jednego wielkiego systemu. Każdy wpis jest rodziną mechanizmów, którą należy rozbić na falsyfikowalną hipotezę. `Tani test` ma odsiać wersję naiwną; pozytywny wynik nie promuje całej rodziny. Zarejestrowane hipotezy i ich aktualne prawdopodobieństwa są w `research/hypothesis_events.jsonl`.

## Reprezentacja

| ID | Rodzina z manifestu | Kluczowe pytanie | Tani test zabijający naiwną wersję |
|---|---|---|---|
| R01 | Learned semantic structures | Czy struktura pojawi się bez etykiet niosących ontologię? | Usuń nazwy relacji i sprawdź held-out kompozycje oraz stabilność prymitywów. |
| R02 | Object-centric computation | Czy system odkryje trwałe obiekty i zmienne z obserwacji? | Zamień wygląd/identyfikatory obiektów i mierz transfer relacji. |
| R03 | Sparse distributed memory | Czy pojemność rośnie bez gwałtownej interferencji i pełnego cleanup scan? | Capacity curve przy stałym rozmiarze stanu i rosnącej liczbie podobnych rekordów. |
| R04 | Hyperdimensional computing | Czy binding/unbinding zachowa kompozycję przy wielu superpozycjach? | Rosnąca liczba bindings, głębokość i identyczny budżet pamięci. |
| R05 | Vector symbolic architectures | Czy algebra struktur uczy się z danych zamiast być w pełni ręczna? | Ablacja gotowych operatorów i unseen recombination. |
| R06 | Symbolic–continuous hybrids | Czy ciągła percepcja i dyskretne reguły można uczyć end-to-end bez kruchego bottlenecku? | Szum percepcyjny, nowe symbole i porównanie z czystymi kontrolami. |
| R07 | Automatically discovered representations/primitives | Czy te same prymitywy są użyteczne w wielu zadaniach? | Cross-task transfer i stability/alignment między seedami. |

## Topologia i wykonywanie obliczeń

| ID | Rodzina z manifestu | Kluczowe pytanie | Tani test zabijający naiwną wersję |
|---|---|---|---|
| C01 | Dynamically constructed computational graphs | Czy topologia śledzi zależności zadania, a nie rozmiar całego stanu? | Stałe lokalne pytanie, rosnący nieistotny graf, licz aktywne węzły i routing. |
| C02 | Graph rewriting systems | Czy skończona reguła daje poprawną normalną postać bez eksplozji? | Krytyczne pary, kolejność rewrite'ów i liczba stanów pośrednich. |
| C03 | Learned rewrite systems | Czy reguły są odkrywane i transferują, nie tylko zapamiętują? | Nowe symbole i kompozycje; ablacją reguł; kontrola ręczna. |
| C04 | Recursive computation | Czy rekurencja ekstrapoluje głębokość poza trening? | Trenuj na małym D, testuj geometrycznie większe D. |
| C05 | Adaptive-depth computation | Czy liczba kroków odpowiada koniecznej pracy? | Wspólny rozmiar wejścia, różna minimalna głębokość rozwiązania. |
| C06 | Recurrent micro-models | Czy mały współdzielony operator zachowuje stan i algorytm przy długim rollout? | Length extrapolation, error accumulation i matched fixed-depth. |
| C07 | Dynamical systems | Czy trajektoria reprezentuje obliczenie odpornie na zakłócenia? | Perturbacje stanu, basin size, czas zbieżności i OOD. |
| C08 | Continuous-time computation | Czy event count jest niższy bez ukrytego kosztu integratora? | Różne tolerancje solvera i raport faktycznych ewaluacji funkcji. |
| C09 | Attractor systems | Czy pojemność i basin recovery skalują się bez spurious attractors? | Rosnąca liczba wzorców, korupcja i liczba iteracji. |
| C10 | Energy-based systems | Czy energia kieruje do poprawnej struktury, a nie tylko zgodnej lokalnie? | Kontrastowe fałszywe minima i mieszanie przy rosnącym K. |
| C11 | Cellular automata | Czy proste lokalne reguły wykonują abstrakcyjne operacje? | Zmiana rozmiaru/topologii oraz porównanie z ręcznym algorytmem. |
| C12 | Neural cellular automata | Czy uczona reguła działa rzadko i transferuje poza siatkę treningową? | Pełny sweep kontra event queue na większych światach. |
| C13 | Spiking computation | Czy liczba spike'ów i energia-proxy maleją przy tej samej jakości? | Event count, czas, sparsity i kontrola recurrent na tym samym zadaniu. |
| C14 | Neuromorphic systems | Czy przewaga pozostaje po uwzględnieniu mapowania na dostępny hardware? | Najpierw symulacja z pełnym kosztem; hardware dopiero po sygnale algorytmicznym. |
| C15 | Event-driven computation | Czy liczba zdarzeń zależy od regionu przyczynowego? | Rosnący uśpiony stan i adversarial event storms. |
| C16 | Local/asynchronous computation | Czy asynchronia zachowuje spójność i determinizm decyzji? | Losowe kolejności aktualizacji, konflikty i koszt synchronizacji. |

## Programy, reguły i algorytmy

| ID | Rodzina z manifestu | Kluczowe pytanie | Tani test zabijający naiwną wersję |
|---|---|---|---|
| P01 | Program synthesis | Czy search nie eksploduje po usunięciu gotowych prymitywów? | Search nodes kontra długość programu i silny enumerative baseline. |
| P02 | Program induction | Czy program jest poprawny poza przykładami treningowymi? | Property tests i held-out długości/kompozycje. |
| P03 | Probabilistic programs | Czy niepewność pomaga bez kosztownego globalnego inference? | Calibration i effective sample size kontra koszt. |
| P04 | Evolving programs | Czy mutacje tworzą transferowalne moduły, nie brittle hacks? | Nowa dystrybucja zadań i genealogia zmian. |
| P05 | Evolutionary computation | Czy informacja na ocenę przewyższa search/random? | Matched evaluation budget i learning curve. |
| P06 | Self-modifying programs | Czy modyfikacje zachowują invariants i dają trwałą korzyść? | Sandbox, property tests, rollback i unseen tasks. |
| P07 | Differentiable interpreters | Czy wyuczona instrukcja dyskretyzuje się i ekstrapoluje? | Hard execution po treningu i length OOD. |
| P08 | Learned virtual machines | Czy mały kontroler odkrywa instrukcje wielokrotnego użytku? | Ablacja ISA/library i transfer między algorytmami. |
| P09 | Algorithm discovery | Czy znaleziony algorytm ma lepszą klasę skalowania, nie tylko stałą? | Fit empirical complexity over several orders of magnitude. |
| P10 | Theorem/proof systems | Czy search dowodu korzysta z uczonych lemmas bez utraty weryfikowalności? | Held-out twierdzenia, proof checks i nodes expanded. |
| P11 | Repeated-path compilation | Czy doświadczenie obniża warm cost bez globalnej invalidacji? | Cold/warm, update perturbation, cache bytes i correctness. |

## Pamięć, wiedza i routing

| ID | Rodzina z manifestu | Kluczowe pytanie | Tani test zabijający naiwną wersję |
|---|---|---|---|
| M01 | Persistent structured knowledge | Czy nowy fakt można dodać lokalnie i zachować globalne constraints? | Insert, conflicting update, retention i affected bytes. |
| M02 | Associative memory | Czy content-addressing działa przy podobnych distraktorach? | Adversarial similarity curve i cleanup reads. |
| M03 | Memory-centric computation | Czy kontroler pozostaje mały, a access jest sublinear? | Rosnące K przy stałym problemie; pełne bytes touched. |
| M04 | Dynamic working memory | Czy stan roboczy rośnie z trudnością, nie z całym kontekstem? | Stała D i rosnący nieistotny context. |
| M05 | Sparse modular systems | Czy moduły specjalizują się i kompozycje używają kilku z nich? | Rosnąca liczba dormant modules i OOD composition. |
| M06 | Learned routing | Czy router zachowuje recall przy confusable knowledge? | Similarity distractors, top-k curve i router bytes/FLOPs. |
| M07 | Continual local learning | Czy lokalna aktualizacja nie niszczy powiązanych reguł? | Sekwencja inserts/updates/deletes i retention matrix. |

## Modele świata i kryteria uczenia

| ID | Rodzina z manifestu | Kluczowe pytanie | Tani test zabijający naiwną wersję |
|---|---|---|---|
| W01 | Active inference | Czy wybór obserwacji redukuje koszt nauki i poprawia decyzje? | Matched observation budget kontra passive learner. |
| W02 | Predictive processing | Czy lokalne prediction errors tworzą użyteczne abstrakcje? | Intervention/OOD i ablacją hierarchy. |
| W03 | Causal world models | Czy model odpowiada na interwencje, nie tylko korelacje? | Observationally equivalent, interventionally distinct worlds. |
| W04 | Predictive state representations | Czy kompaktowy stan wystarcza do przyszłych decyzji? | Minimal-state world, history distractors i planning. |
| W05 | Compression-driven intelligence | Czy krótszy opis przewiduje transfer, a nie tylko dopasowanie? | MDL kontra OOD performance i losowe kompresowalne artefakty. |
| W06 | Minimum-description-length systems | Czy kara za złożoność wybiera prawidłową regułę generującą? | Rival programs o podobnym fit, różnym generalization. |
| W07 | Probabilistic/causal hypothesis competition | Czy konkurujące wyjaśnienia zachowują kalibrację i są szybko odrzucane? | Controlled ambiguity, interventions i posterior cost. |

## Pokrycie pozostałych idei manifestu

- modular systems i mixtures of symbolic/continuous systems są pokryte przez M05 oraz R06;
- causal reasoning, planning i predictive states są pokryte przez W03–W04;
- automatically discovered reasoning operations są celem P02, P08, P09 i R07;
- confidence/energy propagation jest testowane w C09–C10 oraz W07;
- language-as-interface jest osobną bramą G6 w `docs/ROADMAP.md`, nie wczesnym substratem;
- całkowicie nowe abstrakcje pozostają dozwolone, ale wymagają tego samego ledgera, baseline'ów i testu zabijającego.

## Zasady generowania nowych kombinacji

Nowa architektura powinna mieć jawny wektor wyborów:

```text
representation × memory × router × transition/operator × learning rule
× halting/scheduler × output interface × accounting boundary
```

Łączyć wolno dopiero składniki, które osobno wykazały przewidywaną sygnaturę. Wyjątkiem jest eksperyment jawnie prerejestrowany jako test interakcji. Pomysły „całkowicie nowe” trafiają najpierw do ledgera z najtańszą obserwacją, która mogłaby je zabić.
