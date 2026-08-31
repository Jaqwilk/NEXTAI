# GEN-0 literature review — 24 completed experiments

Ten cykli po ostatnim obowiązkowym przeglądzie nie są potrzebne: konfiguracja wymaga literature review co sześć ukończonych eksperymentów, więc ten wake jest review-only. Nie utworzono planu, benchmarku ani scored run. Przejrzano 24 niezmienne wyniki, bieżący Pareto oraz pięć nowych prac pierwotnych `SRC-0048`–`SRC-0052`.

## 1. Co obiektywnie ustalono?

- Lokalne wykonanie może mieć zerowy lub mały slope względem nieistotnego K, ale we wszystkich dodatnich rodzinach struktura potrzebna do selekcji była dostarczona, łatwo identyfikowalna albo kupiona liniowym raw scan, fit/state lub dokładnym search.
- EXP-0023 i wieloseedowy EXP-0024 replikują dependency-aware reuse: przy tym samym kompletnym normalizerze ślad oszczędzał `32–128` update ops i `96–384` workload ops w każdej trudnej komórce, zachowując `432/432` exact i zero false reuse.
- Ten zysk nie jest dominacją. Warm work whole-result i dependency był identyczny, a dependency używał `4.384–5.718×` peak state. Formalny front EXP-0024 zawierał tylko target-valued oracle; implementowalny front zachował kilka klasycznych kompromisów.
- Spośród testowanych nauczycieli reprezentacji żaden system nie wykazał jednocześnie: learned acquisition, exact OOD transfer, małego pełnego kosztu i przewagi nad silnym klasycznym solverem.

## 2. Które założenia zostały sfalsyfikowane?

- Sama sparsity, lokalność, recurrence, energy relaxation, program memory lub semantic cache nie tworzy następcy LLM. Po pełnym rozliczeniu zwykle pojawia się lookup, oracle-equivalent struktura, liniowy preprocessing albo klasyczna dominacja.
- Cross-structure hit nie dowodzi odkrycia semantyki. EXP-0024 osiągnął go przez kompletną ręcznie podaną algebrę i supplied atom identity.
- Niski query cost nie wystarcza: exact-key, program-library i module experiments wielokrotnie przenosiły koszt do fit, state, update lub do stabilnego identyfikatora.
- Przybliżone podobieństwo nie jest bezpiecznym kluczem cache. Następny system musi oddzielić propozycję dopasowania od decyzji o exact reuse i mieć poprawny fallback.

## 3. Co się zreplikowało?

- Replikuje się klasyczna amortyzacja: memoization, indeksowanie, program search plus cache, Rete/event queues i dependency traces obniżają powtarzaną pracę, gdy poprawna struktura jest znana.
- Replikuje się pełnosystemowe ograniczenie HYP-0012: K-independent active execution współistnieje z K-dependent raw access, fit/state, routing lub acquisition.
- Replikuje się brak odrębnej przewagi learned implementation nad matched symbolic control w rodzinach causal, modular, program induction i trace compilation.
- Nie zreplikowano jeszcze learned semantic identity na nowych aliasach ani nowej teorii rewrite; to jest obecny brakujący eksperyment, nie pozytywny fakt.

## 4. Czy portfolio utkwiło w jednej rodzinie?

Nazwy rodzin są zróżnicowane, ale wspólny problem jest ten sam: agent testuje małe, jawne światy dyskretne i często dostarcza interfejs, który niesie rozwiązanie. Kolejny test może pozostać mały tylko jako falsyfikator acquisition; nie wolno po nim dalej stroić additive DSL. Wynik null/negative ma natychmiast uśpić HYP-0011 i wymusić radykalny pivot do nietablicowego wejścia.

## 5. Czy optymalizujemy szczegóły zamiast zasad?

Ryzyko jest wysokie. Kolejna wersja normalizatora, cache policy lub balansowanie stałych byłaby optymalizacją implementacji. Jedyny uzasadniony ruch to usunięcie supplied atom identity — zmiana fundamentalnego czynnika przy zachowaniu silnych whole-result, exact-constraint i oracle controls. Kod ma ograniczyć się do jednego małego benchmarku, współdzielonego alignera i cienkich adapterów.

## 6. Jaki wynik najbardziej zmieniłby przekonania?

Najbardziej zmieniłby je exact, collision-free reuse na nowym episode-specific codebooku i niewidzianej kombinacji rewrite, gdy learned matcher:

- nie otrzymuje stabilnych nazw ani mapowania;
- utrzymuje reuse precision `1.0`, ma niezerową coverage i bezpiecznie fallbackuje;
- pozostaje niedominowany po naliczeniu fit, raw scan, pair matching, verification, state i update;
- wygrywa z exact constraint matcherem nie tylko noisy latency, lecz zarejestrowanymi operacjami przy wzroście liczby konfuzorów.

Brak któregokolwiek z tych punktów silnie obniży HYP-0011. Sam approximate similarity score nie zmieni przekonań.

## 7. Które prace zawierają pozorną nowość?

- `SRC-0048`, [Graph Matching Networks](https://proceedings.mlr.press/v97/li19d.html), już uczy independent embeddings i pairwise cross-graph attention dla podobieństwa grafów. NEXTAI musi mierzyć exact equivalence, false reuse i koszt dopasowania, nie ogłaszać learned matching jako nowości.
- `SRC-0049`, [End-to-End Differentiable Proving](https://arxiv.org/abs/1705.11040), już uczy miękkiej unifikacji symboli i reguł w dostarczonym proverze. Najbliższa kontrola to soft alias matcher, nie kolejna arbitralna sieć.
- `SRC-0050`, [Differentiable ILP](https://doi.org/10.1613/jair.5714), pokazuje uczenie jawnych reguł z przykładów i odporność na szum, ale przestrzeń logiczna i koszt jej przeszukiwania należą do granicy systemu.
- `SRC-0051`, [Neural Logic Machines](https://openreview.net/forum?id=B1xY-hRctX), raportuje perfect size generalization, lecz dostarcza predykaty, connectives, quantifier-like operators i limit arności. To pozytywny neural-symbolic baseline oraz kontrola ontology leakage.
- `SRC-0052`, [Neural Theorem Provers Do Not Learn Rules Without Exploration](https://arxiv.org/abs/1906.06805), pokazuje niepowodzenie recovery dla relacji rozmiaru 2/3 i degradację przy większej liczbie predykatów; exploration poprawia wynik. Następny benchmark musi więc skalować konfuzory i raportować każdy seed, a nie tylko fact accuracy.

## 8. Który następny test ma najwyższą wartość informacji?

Jeden `quick` opaque-alias representation-acquisition test dla HYP-0011. Każdy epizod losuje nowy codebook atomów; mały support z wielu nakładających się wyrażeń czyni mapowanie identyfikowalnym, ale nie podaje go. Query używa niewidzianej kombinacji asocjacji, komutacji, shared-expression split i near-equivalent zmiany. K skaluje liczbę relacyjnie podobnych konfuzorów.

Minimalne kontrole: random/no-reuse, exact-key, independent learned embedding, pairwise soft-unification matcher, exact constraint aligner, whole-result cache z tym samym matcherem, dependency trace z tym samym matcherem oraz symbolic mapping oracle. Learned reuse musi używać abstention/fallback; primary metrics to exact answer, reuse precision/coverage, false reuse, fit/alignment/verification/query/update/workload ops, state i K/D slopes.

Pozytywny wynik pozwala tylko na jedno adversarial replication. Null/negative albo dominacja exact constraint alignera ustawia HYP-0011 `dormant`. Nie dodawać nowej zależności, ogólnego frameworka ani zewnętrznego modelu.

## Decyzja portfelowa

- Żadna hipoteza nie przechodzi do `promising` ani `promoted`.
- HYP-0011 pozostaje `testing` przy confidence `0.68`, ale ma już tylko jeden quick acquisition test przed obowiązkowym `dormant` na null/negative.
- HYP-0012 pozostaje `testing` przy `0.78`; literatura wzmacnia jego przewidywanie o kosztach search/exploration, lecz nie rozstrzyga open-world lower bound.
- Następny wake może prerejestrować tylko powyższy test. Nie wykonywać drugiego eksperymentu w tym samym wake.
