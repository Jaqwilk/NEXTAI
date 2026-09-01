# OBSERVATION

Cykl 237 jest wyłącznie syntezą istniejących dowodów. Nie utworzono hipotezy,
planu, kandydata, benchmarku, schematu ani seeda i nie wykonano scoringu.
Aktywny benchmark pozostaje bez zmian:
`heldout_repository_sequence_compression_v6`.

Zbiór dowodowy obejmuje:

- 98 ukończonych wpisów eksperymentalnych i 855 wierszy kandydatów w ledgerze;
- 101 analiz: 98 analiz wyników z ledgeru oraz trzy analizy post-seed bez
  ukończonego wyniku (`EXP-20260830-0055`, `EXP-20260830-0058`,
  `EXP-20260901-0047`);
- 58 najnowszych stanów hipotez: 35 `falsified`, 22 `dormant` i jedna
  `testing`; jedyna `testing`, HYP-0012, jest kontrolą accountingową, nie
  generatorem architektury;
- pełny inventory 184 wcześniejszych review i 133 service checks sprzed tego
  cyklu, wraz z przeglądami portfela, identifiability gates, preflightami,
  invalidacjami i kontrolami semantycznymi;
- cztery ukończone wyniki terminalnie wykluczone z nauki:
  `EXP-20260830-0046`, `EXP-20260830-0047`, `EXP-20260831-0004` i
  `EXP-20260901-0002`.

Invalidacje nie są traktowane jako porażki mechanizmów. `EXP-0046/0047`
miały niewłaściwą semantykę obowiązkowych kontrolek, `EXP-20260831-0004`
nie wykonał obowiązkowych ról przez wspólny błąd fallbacku, a
`EXP-20260901-0002` nie agregował wymaganej metryki. Dodatkowo
`EXP-20260830-0055`, `EXP-20260830-0058` i `EXP-20260901-0047` są zachowaną
historią awarii bez naukowego wyniku. Późniejsze bramki semantyczne,
atomowe supervisor artifacts, domeny metryk i preflight certificate zamknęły
te konkretne długi infrastrukturalne.

Wynik syntezy jest opisowy i przyczynowy tylko na poziomie hipotez roboczych.
Wiele quicków ma jeden seed. Siła wniosku pochodzi z replikacji podobnego
wzorca w różnych rodzinach i z source-identical ablations, a nie z formalnej
meta-analizy wspólnej metryki.

# FAILURE TAXONOMY

Użyte kody przyczyn:

| Kod | Przyczyna główna |
|---|---|
| RC1 | granica informacji/identyfikowalności: publiczne obserwacje nie wyznaczają wymaganej struktury albo benchmark przekazuje ją w zbyt łatwej postaci |
| RC2 | klasyczna statystyka wystarczająca lub dokładny algorytm realizuje tę samą funkcję taniej |
| RC3 | proxy fit/selection/credit nie wybiera reprezentacji użytecznej OOD; frozen, shuffled, disabled albo prostszy wariant wygrywa |
| RC4 | koszt acquisition, fit, verification, state i maintenance nie amortyzuje oszczędności query |
| RC5 | lokalność/rzadkość jest osiągnięta dopiero po uzyskaniu poprawnego adresu lub stanu; bez niego jakość znika |
| RC6 | iteracja, recurrence albo self-conditioning wzmacnia błąd lub nie zachowuje wystarczającego stanu poza trenowaną głębokością |
| RC7 | regularność działa wewnątrz rodziny, lecz nie istnieje użyteczny source-identical invariant między rodzinami |

Poniższa tabela przypisuje przyczynę pierwotną. Przyczyny wtórne są jawne;
nie należy sumować wierszy jak niezależnych prób.

| Eksperymenty | Primary | Secondary | Co przetrwało mimo porażki |
|---|---|---|---|
| `EXP-20260830-0002/0005/0009` | RC4 | RC2 | exact warm reuse, adaptacyjna liczba kroków i learned macro search działały lokalnie |
| `EXP-20260830-0003/0032` | RC5 | RC3, RC6 | kompozycyjna pamięć i routing miały sygnał, lecz cleanup/stan rosły z K i traciły jakość |
| `EXP-20260830-0006/0010/0019/0021` | RC2 | RC5 | routing, event queue i agenda dawały niski koszt aktywnego fragmentu, ale były indeksem, BFS lub Rete z narzutem |
| `EXP-20260830-0008/0014` | RC1 | RC7 | makro lub faktoryzacja działały po usunięciu niejednoznaczności; pierwotny wynik nie izolował wymaganej przyczyny |
| `EXP-20260830-0018/0033/0034` | RC2 | RC5 | równoległy cleanup, near-zero K slope i sparse execution były realne; klasyczny decoder/tablica przejść były tańsze |
| `EXP-20260830-0020/0025` | RC1 | RC3, RC4 | oracle potwierdzał rozwiązywalność po podaniu reprezentacji; koszt jej pozyskania lub brak informacji był decydujący |
| `EXP-20260830-0022` | RC3 | RC1, RC4 | latent VM dawał częściowe dopasowanie, lecz nie odzyskał programu ani depth transfer; exact MDL pokazał, że dane były wystarczające |
| `EXP-20260830-0026/0027/0028/0029/0030/0031/0035/0038/0040/0044/0056` | RC2 | RC3, RC4, RC5 | motywy, małe stany, aktywne probes, halting, canonicalization i tractable inference działały, lecz trigram/suffix, AR, timed automaton, certified tree, CSSR, transition gate, exact canonicalization, Chow–Liu, CTW lub MDL wyjaśniały efekt taniej |
| `EXP-20260830-0041/0042/0048/0050/0052` | RC7 | RC1, RC6 | naprawy readoutu poprawiały część rodzin, ale pooled learner nie przenosił użytecznej reprezentacji do wszystkich światów |
| `EXP-20260830-0043` | RC3 | RC7, RC1 | online update i prequential boundary działały technicznie; fixed LMS i independent selection były lepsze |
| `EXP-20260830-0053` | RC6 | RC3 | bounded simultaneous rounds miały małą critical path, lecz self-filled context pogarszał loss |
| `EXP-20260830-0057` | RC1 | RC4, RC7 | operator equations dały exact K=32, ale low-support transfer miał minimum zero i meta-fit był droższy od exact MDL |
| `EXP-20260830-0059` | RC7 | RC2, RC3 | pooled low-rank regularization pomagała częściowo, lecz RLS/pooled controls były lepsze i foreign-family transfer nie wystąpił |
| `EXP-20260831-0001/0002/0005/0008/0009` | RC7 | RC1, RC3, RC5 | stabilność, bounded residuals, index i local update działały w części komórek; foreign-only przegrywał z support-only, zwłaszcza na N-CMAPSS/DS08a |
| `EXP-20260831-0003` | RC3 | RC6, RC7 | legalna convex mixture pozostała skończona, lecz słaby atom destabilizował rollout i wagi nie transferowały |
| `EXP-20260901-0003/0020/0021/0034` | RC4 | RC2 | krótszy warm prefix, tree contraction, persistent macros i dyadic compilation dawały prawdziwy sygnał wykonawczy, ale przenosiły koszt do fit/update/state |
| `EXP-20260901-0036/0045/0059` | RC4 | RC2, RC3 | learned exact guidance zmniejszał search nodes lub poprawiał incumbent/bound, lecz frozen guidance wygrywał pełnym kosztem |
| `EXP-20260901-0004/0022` | RC5 | RC3 | sparse update/active cone dawały zero K slope; persistence lub affine ridge zachowywały lepszą jakość taniej |
| `EXP-20260901-0007/0011/0013/0017` | RC3 | RC2, RC5, RC6 | local credit, sparse code, routing i lifting miały małe efekty; frozen, all-expert lub single-scale source-identical role obalał deklarowaną przyczynę |
| `EXP-20260901-0009/0027/0032/0062` | RC6 | RC3, RC2, RC4 | bounded state, recursion lub grammar/selection działały mechanicznie, lecz memoryless/one-pass/Re-Pair/PPM/CTW były jakościowo lepsze |
| `EXP-20260901-0024/0029` | RC3 | RC6, RC2, RC5 | future-supervised state i event gating dawały dodatni kontrast do własnej ablacji; control bank albo frozen transition nadal wygrywał |
| `EXP-20260901-0030/0031` | RC2 | RC3 | aktywne sensing i skompilowana ścieżka zmniejszały probes/work, ale learned likelihood/utility nie dawały przewagi nad Gaussian/kernel/fixed utility |
| `EXP-20260901-0033` | RC1 | RC5 | antisymmetric local execution miało zero K slope, lecz publiczna nonlinear encoding nie zachowywała narzuconej symetrii |
| `EXP-20260901-0037/0038` | RC3/RC7 | RC1, RC5 | selection i invariant modules były source-identical i stabilne; fitness/stability nie przewidywały OOD, a common invariant nie powstał |
| `EXP-20260901-0044` | RC6 | RC7 | stack depth transfer przeżył relabeling i nowy corpus, lecz exact rule nie wykonał innej, recoverable operacji |
| `EXP-20260901-0048/0049/0051/0054` | RC3 | RC5, RC6 | local credit, partitioning, bottleneck i learned address miały lokalne efekty; dense/shuffled/frozen wariant był równy lub lepszy OOD |
| `EXP-20260901-0056` | RC2 | RC3, RC4 | local insertion, bounded search i R1 break-even były realne; frozen encoder i raw k-d tree były dokładniejsze i tańsze |
| `EXP-20260901-0057` | RC7 | RC1, RC2, RC5 | sparse access oszczędzał część query work, lecz żaden learned role nie osiągnął użytecznego transferu; Chow–Liu osiągnął 0.9844 accuracy |
| `EXP-20260901-0060` | RC3 | RC6, RC5 | bounded slot-local particle state działał; posterior mean i persistence były lepsze od learned proposal |

Wyniki dodatnie lub kalibracyjne pozostają częścią datasetu, ale nie są
przepisywane na „porażki”: `EXP-20260830-0001/0004` kalibrowały aparaturę;
`EXP-20260830-0007/0011/0012/0013/0015/0016/0017/0023/0024`,
`EXP-20260831-0006/0007` oraz `EXP-20260901-0041/0042` zachowały wąskie
pozytywne sygnatury. Ich failed promotion gates są uwzględnione w RC1, RC2
lub RC4. `EXP-20260830-0051`, `EXP-20260901-0015`,
`EXP-20260901-0039/0040` były niedyskryminujące przez crash lub brak kompletnej
kontrolki; późniejsze dzieci rozstrzygnęły odpowiednie reguły bez
reinterpretacji rodziców.

# REPEATED ROOT CAUSES

## RC1 — dylemat obserwowalności i klasycznej wystarczalności

Gdy publiczne dane zawierały mocny symmetry breaker, komplet interwencji,
stabilne pary albo mały zamknięty język, prosty exact/statistical control
odzyskiwał strukturę. Gdy te podpory usuwano, learned representation przestawał
być identyfikowalny albo transferował tylko przypadkową regularizację. Wzorzec
powtarza się w programach, causal factorization, cross-family continuous,
entity binding i local dynamics. Evidence jest wysokie jako opis granicy
obecnych kontraktów, ale nie jest twierdzeniem o wszystkich możliwych danych.

Kontrprzykład: `EXP-0015/0016` oraz `EXP-20260901-0041/0042` pokazują, że
learned structure może być poprawna i ekstrapolować, gdy obserwacje wyznaczają
małą strukturę. Ograniczenie kontrprzykładu jest zarazem sednem RC1: finite
intervention library lub siedmiosymbolowa gramatyka dostarczała wystarczający
most. Typ: informacyjny, benchmarkowy, reprezentacyjny; potencjalnie
fundamentalny tylko dla danego observation boundary.

## RC2 — learned route redukuje się do znanego algorytmu

Rete/BFS, timed automata, CSSR, Chow–Liu, context trees, exact constraints,
MDL, k-d trees, bit flipping i klasyczne likelihoods wielokrotnie realizowały
tę samą funkcję z mniejszym kosztem. To najsilniejszy ilościowo pattern:
dotyczy dyskretnych programów, probabilistyki, sekwencji, active sensing,
cellular execution i retrieval. Nie znaleziono pełnosystemowego kontrprzykładu.
`EXP-0033` i `EXP-20260901-0036` miały węższy query/search-node win, ale
przegrywały R16/full cost. Typ: reprezentacyjny, algorytmiczny, asymptotyczny.

## RC3 — proxy treningowe nie wybiera użyteczności OOD

Frozen, shuffled, recurrence-disabled, one-sweep, single-scale, posterior-mean
albo support-only role często był lepszy mimo tego samego źródła i pojemności.
Powtarzało się to dla routing keys, split fitness, bottleneck coordinates,
credit traces, update rates, grammar votes, particles i state selection.
To mocniejsze niż samo „underfitting”: source-identical interwencja często
odwracała znak efektu. Kontrprzykład: WT recurrent residual w
`EXP-20260831-0006/0007` i pushdown w `EXP-20260901-0041/0042` miały użyteczny
learned signal, lecz pierwszy nie transferował rodzinowo, a drugi nie przeżył
adversarial operation. Typ: optymalizacyjny i reprezentacyjny.

## RC4 — oszczędność query nie spłaca discovery

Macro discovery, canonicalization, learned compilation, exact guidance,
certification, learned indexes i dyadic kernels zmniejszały wybrany licznik,
ale acquisition, fit, verification, state, update lub input traversal kasował
zysk. Wzorzec powtarza się od `EXP-0002` do `EXP-20260901-0059` w co najmniej
czterech niezależnych rodzinach. Kontrprzykłady są wąskie: exact memo i
dependency reuse osiągały warm savings, lecz korzystały ze stabilnego klucza
lub ręcznej normalizacji i nie pokonały mocnego klasycznego controlu po pełnej
granicy. Typ: asymptotyczny i systemowo-ekonomiczny.

## RC5 — lokalny compute jest downstream od poprawnego adresu/stanu

Active-cone, sparse expert, event queue, bounded lookup i slot-local update
często dawały zerowy K slope. Gdy indeks lub causal cone był dostarczony,
sygnatura była czysta; gdy miał zostać nauczony, kolizje, zły routing albo
utrata stanu obniżały jakość. Jest to przyczyna zależności, nie osobny objaw:
lokalność oszczędza dopiero po rozwiązaniu RC1/RC3. Kontrprzykłady
`indexed_graph`, exact active cone i raw k-d tree potwierdzają właśnie ten
warunek. Typ: informacyjny i asymptotyczny.

## RC6 — learned state/feedback nie zachowuje wymaganych rozróżnień

Recurrent mixing, iterative self-filling, energy relaxation i recursive
rollout wielokrotnie akumulowały błąd; memoryless lub one-pass ablation był
lepszy. Pattern jest mocny, ale nie uniwersalny: WT residual state i learned
pushdown ekstrapolowały w swoich wąskich domenach. Dlatego zamknięte są
konkretne state rules, a nie recurrence jako całość. Typ: reprezentacyjny i
optymalizacyjny.

## RC7 — brak portable invariant między rodzinami

Low-rank operators, bounded residuals, convex priors, predictive indices,
learned update rates, recurrent states, invariant modules i sparse set memory
nie pokonały foreign-only versus support-only. Najmocniejszy kontrast daje WT:
`EXP-20260831-0006/0007` replikuje realny within-source efekt, a
`EXP-20260831-0008` traci go po family-blind transfer. `EXP-20260830-0046`
jest wykluczony i nie wzmacnia tego wniosku. Brak pełnego kontrprzykładu:
disjoint-corpus pushdown jest transferem w tej samej reprezentacji problemu,
nie między rodzinami. Typ: informacyjny i reprezentacyjny.

# CROSS-FAMILY EVIDENCE

Najsilniejszy spójny wniosek brzmi: pooling może regularizować, lecz nie jest
dowodem transferu. `shared > independent` czasem zachodziło, ale
`cross-family-only > support-only` nie przeszło we wszystkich rodzinach.
Dotyczy to:

- czterorodzinnych reprezentacji SVD/pointer/recurrent/dictionary/fragment
  (`EXP-20260830-0041/0042/0048/0050/0052`);
- operatorów i mechanizmów (`EXP-20260830-0056/0057`);
- trzech realnych continuous families
  (`EXP-20260831-0001/0002/0003/0005/0008/0009` oraz
  `EXP-20260901-0038`);
- czterorodzinnej sparse set memory (`EXP-20260901-0057`).

N-CMAPSS/DS08a często ujawniał negative transfer, ale wzorzec nie zależy od
jednego datasetu: program composition i local dynamics również się zapadały w
czterorodzinnych kohortach. Evidence jest wysokie dla dotychczasowych
source-identical kontraktów, niskie dla tezy, że transfer jest niemożliwy w
ogóle. Nie przetestowano naturalnego wspólnego observable, który spełniałby
warunki identyfikowalności bez nazw rodzin lub ręcznej ontologii.

# SURVIVING POSITIVE SIGNATURES

| Sygnatura | Najmocniejsze dowody | Ograniczenie |
|---|---|---|
| query work słabo zależny od dormant K | indeksy, active cone, event execution, addressing, bounded state | zwykle wymaga gotowego adresu/struktury albo traci matched quality |
| warm inference maleje z doświadczeniem | `EXP-0002`, `EXP-0023/0024`, `EXP-20260901-0003/0021` | discovery, input scan, state lub invalidation nie amortyzują się pełnosystemowo |
| local/slot-only update | adaptive index, WT residual, predictive index, entity insertion, particles, SSM | nie gwarantuje transferu ani lepszej jakości |
| reusable learned operation | macro library `EXP-0007–0009`, operator equations `EXP-0057`, exact guidance | finite language, exact classical control lub pełny koszt blokuje promocję |
| systematic depth extrapolation | pushdown `EXP-20260901-0041/0042` | przegrywa inną recoverable operation w `EXP-0044`; wynik jest wąski |
| real within-family recurrent benefit | WT `EXP-20260831-0006/0007` | nie przenosi się family-blind w `EXP-0008` |
| safe learned fast path with exact fallback | `EXP-20260901-0036/0045/0059` | poprawność zachowana, lecz frozen guidance jest tańszy |
| learned selection ma mierzalny efekt | population, routing, partition, input selection | znak efektu nie jest stabilny OOD i często shuffled/frozen wygrywa |

Te sygnatury są warte zachowania jako kontrole i wymagania przyszłych testów.
Żadna nie jest sama w sobie oficjalnym kandydatem na następcę LLM.

# CLOSED BOTTLENECKS

`CLOSED` oznacza zamknięcie konkretnej tezy, nie twierdzenie o całej klasie
matematycznej.

1. **Sparse/local/parallel execution jako samodzielna nowość.** Event queue,
   active cone, sparse experts, contraction i local updates są wartościowymi
   technikami, lecz bez learned relevance nie dają użytecznego full-cost win.
2. **Learned alias znanego sufficient statistic.** Kolejny learner, który po
   fit implementuje Chow–Liu, CTW, CSSR, timed automaton, k-d tree, Rete,
   bit-flipping lub exact MDL, nie jest nową zasadą bez odmiennej mierzalnej
   sygnatury.
3. **Pooling lub parameter sharing jako dowód transferu.** Bez foreign-only
   versus support-only i family-wise gain ten wniosek jest zamknięty.
4. **Query-only asymptotics jako dowód ekonomii systemu.** Fit, acquisition,
   verification, state, bytes, update i workload muszą pozostać w granicy.
5. **Rescue exact rules przez tuning po wyniku.** Wszystkie 35 `falsified` i
   dokładne `dormant` reguły pozostają zamknięte w swoich prerejestrowanych
   postaciach.
6. **Invalid result jako evidence.** Cztery ukończone invalidacje i trzy
   post-seed non-results są wyłącznie historią diagnostyczną.

# UNRESOLVED BOTTLENECKS

Trzy pozostałe niewiadome tworzą łańcuch, a nie trzy propozycje architektur:

```text
candidate-visible experience
        | U1: czy użyteczna wspólna struktura jest identyfikowalna?
        v
task-relevant sufficient state
        | U2: czy frozen proxy potrafi wybrać stan użyteczny OOD?
        v
matched-quality local/reusable computation
        | U3: czy pełny koszt pozyskania i utrzymania się amortyzuje?
        v
full-system capability-per-cost advantage
```

## U1 — identifiable, transferable quotient

Nie wiadomo, czy istnieje naturalny candidate-visible signal, który wyznacza
task-relevant strukturę wspólną dla różnych światów, ale nie przekazuje gotowej
ontologii i nie jest już prostą klasyczną statystyką wystarczającą. RC1 i RC7
są bardzo mocne w obecnych kontraktach, lecz obecne kontrakty mogą usuwać
właśnie informację potrzebną do transferu. Status: `UNRESOLVED`.

## U2 — alignment treningowego kryterium z OOD utility

Zakładając, że potrzebna informacja jest publiczna, nie wiadomo, czy istnieje
prospektywnie zamrożone kryterium bez OOD targetów, które wybiera stan,
partition, update lub credit rule zachowujący użyteczne rozróżnienia podczas
rolloutu i transferu. Shuffled/frozen/disabled ablations są mocnym dowodem
przeciw dotychczasowym proxy, ale nie izolują, czy problemem jest brak
informacji (U1), czy zły selector (U2). Status: `UNRESOLVED`.

## U3 — full-cost amortization boundary

Zakładając poprawny użyteczny stan, nie wiadomo, czy istnieje realny workload,
na którym jego observation-learned acquisition, fit, verification, update i
state spłacają się względem najmocniejszego klasycznego controlu, a przewaga
rośnie ze skalą lub reuse. Dotychczasowe horizons mogły być za krótkie, lecz
ich wydłużanie po wyniku byłoby tuningiem. Status: `UNRESOLVED`.

# ALTERNATIVE EXPLANATIONS

- **Za małe modele lub za mało treningu.** Jest to wiarygodne dla pojedynczych
  quicków, szczególnie recurrent/SSM. Nie wyjaśnia jednak, dlaczego frozen lub
  shuffled source-identical role często był lepszy ani dlaczego exact
  classical control odzyskiwał pełną jakość.
- **Benchmarky są zbyt małe i target-shaped.** To prawdopodobnie zwiększa
  przewagę exact controls i zmniejsza horyzont amortyzacji. Z drugiej strony
  real WT, DronePropA, N-CMAPSS i repository bytes odtwarzają część tego samego
  wzorca. Wpływ skali pozostaje `UNKNOWN`, nie jest obaleniem syntezy.
- **Anonymizacja usuwa naturalną semantykę.** To mocna alternatywa dla RC7 i
  właśnie powód pozostawienia U1. Dodanie nazw kanałów lub ręcznej ontologii
  nie rozstrzygnęłoby jednak celu source-identical learning.
- **Classical controls są wyjątkowo dopasowane do mikroświatów.** Częściowo
  prawda. Kontrole są jednak wymagane, ponieważ ujawniają, kiedy generator sam
  dostarcza wystarczającą strukturę. Przyszły kontrprzykład musi pokazać
  mechaniczny składnik, którego control nie ma, nie tylko większy model.
- **Single-seed selection noise.** Ogranicza wnioski o każdy exact mechanism.
  Nie wyjaśnia wielokrotnego odwrócenia znaku przez frozen/shuffled ablations
  ani wieloseedowego braku cross-family transferu.
- **Operation counts nie są kosztem sprzętowym.** `CAL-20260901-0001`
  potwierdza tę niezgodność. Dlatego RC4 dotyczy zadeklarowanej pełnej granicy,
  a nie uniwersalnej prognozy wall-clock dla przyszłego hardware.
- **Selection bias historii.** Portfolio aktywnie wybierało mechanizmy z
  oczekiwaną szansą na lokalny compute signature, więc częstość RC5 może być
  zawyżona. Wniosek o zależności locality od representation pozostaje jednak
  wsparty bezpośrednimi source-identical ablations.

# BELIEF-CHANGING QUESTIONS

1. **U1:** Czy naturalna, candidate-visible zmienność może przy jednej
   zamrożonej granicy informacji wyznaczyć ten sam task-relevant quotient w co
   najmniej trzech niewidzianych światach, podczas gdy złamanie tej zmienności
   usuwa efekt, a mocna klasyczna statystyka nie odzyskuje go taniej?
2. **U2:** Gdy kilka reprezentacji ma podobny development fit i identyczny
   dostęp do danych, czy prospektywnie zamrożony observation-only score potrafi
   konsekwentnie wybrać tę, która zachowuje jakość po OOD rollout/transfer,
   oraz przegrać dokładnie po shuffle tego score?
3. **U3:** Gdy useful learned state jest już potwierdzony przy matched quality,
   czy jego skumulowany pełny koszt przecina koszt najmocniejszego klasycznego
   controlu w z góry zadeklarowanym realnym reuse horizon i czy luka rośnie na
   co najmniej trzech skalach?

Najbardziej rozdzielające evidence jest sekwencyjne: negatyw U1 zatrzymuje U2
i U3; pozytyw U1 z negatywem U2 izoluje selection; pozytywy U1/U2 z brakiem
cost crossover izolują U3.

# LITERATURE CONTRADICTION TARGETS

Nie wykonano nowego searchu. Następny review ma szukać wyłącznie kontrprzykładów
do trzech tez:

1. **NEXTAI observation:** anonymous cross-family experience jest albo
   nieidentyfikowalne, albo jego wystarczający invariant odzyskuje prosty
   classical control. **Contradiction search:** znaleźć systemy, w których
   learned transferable quotient powstaje z naturalnego observable bez
   semantic labels, ręcznej ontologii lub family routing, i ustalić dokładnie,
   jaki mechaniczny symmetry breaker odróżnia je od NEXTAI.
2. **NEXTAI observation:** development-local fit, likelihood, residual,
   reconstruction, gain lub fitness nie przewiduje OOD recursive utility.
   **Contradiction search:** znaleźć kontrolowane systemy, gdzie zamrożony
   pre-outcome selector kauzalnie wybiera OOD-sufficient state i pokonuje
   shuffled/frozen selector przy tej samej informacji i pojemności.
3. **NEXTAI observation:** learned discovery/fit/certification nie amortyzuje
   się względem matched classical sufficient statistic. **Contradiction
   search:** znaleźć pełnosystemowe wyniki z matched capability, jawnie
   policzonym acquisition/fit/update/state i prospektywnym crossover horizon,
   gdzie learned structure ma lepszą krzywą kosztu, nie tylko niższy koszt
   pojedynczego query.

# DECISION

**B. Istnieją trzy konkurujące, lecz uporządkowane bottlenecks.** Nie ma podstaw,
by arbitralnie uznać jeden z nich za pierwotny. Najbardziej zwarta wspólna
teoria porażek brzmi:

> NEXTAI potrafi tanio wykonywać użyteczną strukturę, ale nie wykazał jeszcze,
> że potrafi ją jednocześnie zidentyfikować z legalnych obserwacji, wybrać przez
> proxy zachowujące utility OOD i spłacić pełny koszt jej pozyskania.

Confidence wynosi `0.90` dla powtarzalności RC2/RC4/RC5, `0.85` dla RC7 w
dotychczasowych kontraktach, `0.75` dla rozdzielenia U1/U2 i `0.70` dla U3 jako
niezależnego bottlenecku zamiast skutku krótkich horyzontów. Confidence jest
`<0.20` dla ekstrapolacji tej teorii na wszystkie możliwe systemy lub skalę
LLM.

Nie ma autoryzowanego następnego eksperymentu. Następny dozwolony krok to jeden
targeted literature-contradiction review dla U1–U3, bez wyboru architektury,
benchmarku i scoringu. Dopiero mechaniczny kontrprzykład może uzasadnić później
jeden test belief-changing; brak kontrprzykładu oznacza dalsze wstrzymanie
architecture scoring, nie wymyślenie kolejnej mikrodomeny.
