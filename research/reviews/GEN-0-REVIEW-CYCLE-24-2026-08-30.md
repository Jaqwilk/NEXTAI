# GEN-0 review — review-only wake po EXP-0023

Zakres: dodatkowy przegląd portfela wyznaczony jawnie przez analizę EXP-0023, wykonany przy `23` ukończonych eksperymentach, czyli o jeden eksperyment wcześniej niż automatyczny interwał 12. Nie utworzono planu, nie zmieniono benchmarku i nie wykonano scoringu. Od poprzedniej refleksji ukończono 11 eksperymentów: 9 quick i 2 screen, obejmujących 6 hipotez. Spośród 72 przebiegów kandydatów 71 ukończyło pracę, jeden crash zachowano; wszystkie 23 wyniki miały poprawną integralność przed i po.

## 1. Czego obiektywnie się nauczyliśmy?

- Lokalna praca może być niezależna od dormant K, gdy istnieje prawidłowa reprezentacja i adresowanie. Powtórzyło się to w pointer execution, causal local dynamics, faktoryzowanym cleanup, indexed modules, active-prefix VM i semantic trace reuse.
- Pełny system zwykle nie zachowuje tej własności. Raw perception miało K slopes `0.488` i `0.610–0.623`, causal oracle z wejściem `0.4485`, dense expert routing `0.9684`, a w innych rodzinach fit, stan lub indeks rosły około liniowo z K.
- Najmocniejszy zreplikowany learned wynik był warunkowy: clean identifiable causal factorization osiągnęła `1.0` w 36 komórkach i trzech seedach, ale noisy/non-exhaustive wariant spadł do `2/48`, podczas gdy dense control miał `27/48` i oracle `48/48`.
- Gotowe programy są łatwiejsze niż ich zdobycie. Pointer learner wykonywał przekazaną sekwencję dokładnie, lecz po usunięciu programu latent VM odzyskała tylko `11/48` prawdziwych maszyn i zużyła `4.751×` więcej cold ops niż exact MDL.
- Osobne moduły, równoległa energia i semantic reactor nie uzyskały odrębnej przewagi nad właściwymi klasycznymi kontrolami. Flat direct program dominował moduły, incremental cleanup był tańszy od parallel energy, a semantic reactor był operacyjnie identyczny z Rete.
- EXP-0023 dał jedyny obecnie otwarty dodatni trade-off: dependency trace przenosił wynik między byte-different izomorficznymi DAG-ami, miał `59.53%` mniej warm ops od full evaluation i `17.58%` tańszy update od whole-result cache, ale używał `2.857×` więcej stanu i korzystał z ręcznej kanonizacji.

## 2. Które założenia zostały sfalsyfikowane?

- Exact wykonanie dostarczonych instrukcji nie jest dowodem learned program induction ani autonomicznego odkrycia algorytmu.
- Czysta, kompletna macierz interwencji przenosiła zasadniczą część sukcesu causal learnera; efekt nie przetrwał jednoczesnego szumu i niepełnego pokrycia.
- Kontener modułu nie dodaje wartości, jeśli identyczna wyspecjalizowana funkcja może być zapisana jako płaski indexed program.
- Jedna równoległa runda nie oznacza mniejszej całkowitej pracy; przyrostowy sekwencyjny harmonogram może wykonać te same lokalne poprawki taniej.
- Chemiczna lub zdarzeniowa terminologia nie odróżnia architektury od Rete, jeśli reguły, matching, agenda i koszty są identyczne.
- Cross-structure cache hit na izomorfizmie nie jest learned semantic compilation. Ręczny canonical key wykonuje reprezentacyjną część zadania.

Nie sfalsyfikowano ogólnej możliwości learned causal models, differentiable machines, energy systems, sparse modules ani semantic compilation. Odrzucono konkretne zamknięte aparaty oraz silniejsze interpretacje, które nie przeszły matched controls.

## 3. Które wyniki się zreplikowały?

- Causal factorization na kompletnej, shortcut-resistant kohorcie: EXP-0015 quick i EXP-0016 screen, trzy seedy, exact recovery i local K-invariance. EXP-0020 wyznacza jej granicę, a nie replikację w trudniejszym świecie.
- Faktoryzowany relational cleanup: EXP-0017 quick i EXP-0018 trzyseedowy screen, exact held-out completion i query K slope `0`; jednocześnie screen potwierdził null względem incremental control.
- K-zależny koszt pełnego input boundary: EXP-0014/15/16/20 oraz EXP-0023 po obowiązkowym skanie wejścia.
- Klasyczna kompilacja obniża warm execution: program-library EXP-0007–0009, MDL VM EXP-0022 i semantic cache EXP-0023.

Nie zreplikowano HYP-0011 między seedami, przez inne klasy przepisań ani przez uczony kanonizator. Nie ma też transferu dodatniego mechanizmu pomiędzy niezależnymi rodzinami zadań ani ślepego holdoutu.

## 4. Czy portfolio utknęło w jednej rodzinie?

Nie według etykiet: od EXP-0013 zbadano VM/pointer, causal state, energy, production reactions, modular routing i semantic traces. Tak według głębszej struktury: wszystkie 23 eksperymenty to małe, widoczne, skończone światy z dyskretnymi tokenami, ręcznie ograniczoną klasą hipotez i symbolicznym oracle. „Opaque” identyfikatory ukrywają nazwy, ale nie zastępują uczenia encji z języka, obrazu lub ciągłego sygnału.

Portfolio ma obecnie 6 hipotez dormant, 4 uncertain i tylko 2 testing. To zdrowo odrzuca słabe kierunki, ale tworzy ryzyko, że HYP-0011 zostanie nadmiernie eksploatowana tylko dlatego, że jest ostatnim dodatnim kandydatem. Jeden adversarial screen jest uzasadniony; seria poprawek cache bez uczenia reprezentacji nie jest.

## 5. Czy optymalizujemy implementację zamiast zasady?

Ryzyko jest wysokie, lecz ostatnie korekty miały wartość rozstrzygającą: screen causal usunął shortcut, noisy cohort złamał identyfikowalność, energy screen dodał incremental control, whole-I/O usunął program supervision, a semantic trace dodał canonical whole-result control. Każda zmiana obniżyła siłę dozwolonego twierdzenia zamiast chronić kandydata.

Nie wolno teraz poprawiać progów causal learnera, optymalizera VM, dispatchu modułów, Rete aliasu ani harmonogramu energii. HYP-0011 zasługuje najwyżej na jeden screen, który zmienia trudność semantycznej równoważności i workload aktualizacji. Jeśli tylko zwiększy cache lub dopisze kolejne ręczne reguły, będzie to strojenie implementacji.

## 6. Jaki wynik najbardziej zmieniłby obecne przekonania?

System musiałby zdobyć lub zweryfikować reprezentację równoważności, a następnie wykorzystać doświadczenie bez fałszywego reuse. Na nowych grafach po asocjacyjnych i strukturalnych przepisaniach powinien zachować exact accuracy, odróżniać prawie równoważne kontrprzykłady, mieć niższy skumulowany koszt przy wielu lokalnych zmianach niż equality-saturation whole-result cache i nie ukrywać kosztu odkrywania reguł, canonicalization, state ani invalidation.

Najbardziej zmieniłby przekonania wynik wieloseedowy, w którym learned lub ogólny dependency compiler pozostaje non-dominated po pełnym workloadzie i pokonuje silny e-graph/content-addressed control. Równie informacyjny negatyw pokaże, że EXP-0023 był wyłącznie klasycznym kompromisem pamięć–update dla ręcznego izomorfizmu.

## 7. Która wcześniejsza praca zawiera pozorną nowość?

| Pozorna nowość | Prior art | Granica twierdzenia |
|---|---|---|
| Learned interpreter i pamięć programu | NTM/DNC, NPI, Differentiable Forth, RobustFill (`SRC-0005`, `SRC-0006`, `SRC-0040`, `SRC-0042`, `SRC-0039`) | Program, sketch, trace i search muszą być jawnie rozliczone. |
| Reusable program fragments | DreamCoder (`SRC-0041`) | Library learning i e-graph refactoring już istnieją; wymagany jest lepszy pełny trade-off. |
| Causal invariant state | `SRC-0018–SRC-0021` | Unknown interventions i invariant mechanisms są znanym polem; toy recovery nie jest nową teorią. |
| Energy/associative reasoning | Hopfield i learned energy methods (`SRC-0025–SRC-0029`) | Completion i iterative minimization są znane; liczy się odrębny koszt i odporność. |
| Semantic reactions | Rete, Chemical Abstract Machine, NPS (`SRC-0030`, `SRC-0031`, `SRC-0033`) | Event matching i rewriting nie są nowością bez mechanizmu wykraczającego poza production system. |
| Sparse modular routing | Routing Networks i sparse MoE (`SRC-0035–SRC-0038`) | Aktywne moduły nie wystarczą; routing, identyfikowalność i bytes są częścią systemu. |
| Dependency-aware semantic reuse | Self-adjusting computation, nominal incremental computation, canonical labeling i e-graphs (`SRC-0043–SRC-0047`) | Lokalna invalidacja i congruence reuse są klasyczne; learned representation lub lepszy Pareto musi być odrębnym sygnałem. |

## 8. Który następny test ma największą oczekiwaną informację?

Najwyższy priorytet otrzymuje jeden trzyseedowy adversarial screen HYP-0011, roboczo `semantic_trace_compilation_adversarial_v2`. Jest to weryfikacja jedynego zaskakującego dodatniego quick, zgodna z hierarchią programu; nie jest promocją.

### Minimalny test rozstrzygający

- K=`8/32/128`, D=`1/4/6/8`, Q=`12`, seedy `1103/2207/3301`, budżet `screen`.
- Cold/warm pary pozostają duplicate-free i bez wspólnych ID, lecz zmieniają topologię przez asocjacyjność, przemienność, neutral elements, constant folding oraz split/merge wspólnych podwyrażeń. Osobny balanced near-equivalent split musi różnić się wynikiem, by wykryć fałszywe reuse.
- Workload zawiera z góry ustalone serie lokalnych zmian i różne query:update ratios. Raportuje cumulative cold/warm/update ops, break-even reuse count, peak cache state, invalidated work, raw bytes, canonicalization/saturation oraz retencję.
- Kontrole: random, exact-key cache, obecny tree-canonical whole-result i dependency cache, content-addressed normalized result cache, equality-saturation/e-graph whole-result control, dependency/e-graph trace oraz uprzywilejowany oracle equivalence. Jeżeli występuje learned rewrite acquisition, jego demonstracje, fit i stan są częścią planu i osobną ablacją.
- Sygnał dodatni: exact w każdym seedzie, zero false reuse, stabilny zysk skumulowanych operacji po prerejestrowanym break-even, dependency-local update i non-dominated full-system Pareto względem e-graph whole-result control. `Promising` pozostaje zabronione, jeśli równoważność jest całkowicie ręczna.
- Sygnał null/negative: silny whole-result/e-graph control dorównuje lub dominuje, state rośnie szybciej niż oszczędzona praca, przewaga znika po kilku zmianach, albo compiler myli near-equivalent grafy. Wtedy HYP-0011 przechodzi do dormant i portfolio musi opuścić cache/DSL.

Kontrakt implementacyjny: nie zmieniać zamrożonego EXP-0023; nowa wersjonowana kohorta ma ponownie użyć możliwie dużej części małego rdzenia, dodać najwyżej jeden normalizer/equality engine i cienkie adaptery, bez nowej zależności, frameworka lub zewnętrznego modelu.

## Decyzja portfelowa

- Żadna hipoteza nie przechodzi do `promising` ani `promoted`.
- HYP-0011 pozostaje `testing` przy confidence `0.62`; dostaje dokładnie jeden screen o powyższym zakresie.
- HYP-0012 pozostaje `testing` i rośnie z `0.73` do `0.76`: EXP-0023 potwierdził rzeczywistą amortyzację, lecz ponownie ujawnił koszt raw input, ręcznej reprezentacji i `2.857×` większego stanu. To jest także jawne ograniczenie pewności sceptycznej tezy.
- Pozostałe rodziny zachowują bieżące statusy. Nie tworzyć nowej hipotezy przed rozstrzygnięciem jedynego dodatniego mechanizmu; po null/negative wymusić radykalny pivot do uczenia reprezentacji z nietablicowego wejścia.
