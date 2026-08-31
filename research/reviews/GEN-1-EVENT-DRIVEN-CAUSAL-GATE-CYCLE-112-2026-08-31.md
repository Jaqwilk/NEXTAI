# GEN-1 — observation-only event-driven causal gate, cykl 112

Zakres: jeden no-scoring design gate po decyzji `select_none` z cyklu 111. Audyt obejmuje
wyłącznie istniejące `causal_intervention_adversarial_v2`,
`active_information_acquisition_v1` oraz `nonstationary_online_update_battery_v1` wraz z ich
immutable planami i wynikami. Nie utworzono hipotezy, planu, seeda, benchmarku, schematu,
kandydata ani nowej zależności. Lab B nie dostarczało evidence.

## Pytanie bramki

Czy bez zmiany danych i schematów można zdefiniować jeden source-identical, observation-only
operator konkurencji hipotez, który jednocześnie:

1. daje matched-quality full-cost scaling dla co najmniej trzech K;
2. aktualizuje wyłącznie lokalnie konkurujące hipotezy bez globalnego retrainingu;
3. ponownie wykorzystuje ten sam odkryty operator na niewidzianym mechanizmie OOD;
4. nie otrzymuje family labels, ręcznej ontologii, gotowego likelihoodu ani semantycznego adaptera.

## Obserwacje interfejsów

| Inventory | Public fit/query/update boundary | K | Obserwowany wynik |
|---|---|---|---|
| `causal_intervention_adversarial_v2` | Fit otrzymuje jawne node-indexed parent pools i epizody z jawnymi intervention-node IDs; query zawiera `root_values`, jawne interwencje i `target` node ID. Kandydat przeszukuje ręcznie ustaloną bibliotekę COPY/NOT/XOR/XNOR/AND/OR. | 8/32/128 | EXP-0012: robust local miał 1.0 accuracy, zerowy query K slope i 1.0 vs 0.083 label ablation w 36 komórkach, lecz fit przy K=128 osiągnął 3.46M ops, a znana topologia, bounded parent pools, jawne routing IDs i gate library blokowały promotion. |
| `active_information_acquisition_v1` | Fit otrzymuje pełny labeled `Codebook`, w którym indeks wiersza jest klasą. Query wykonuje wybrane binarne probes. `CodebookUpdate` jawnie podaje zmienione label IDs i wiersze. | 8/32 | EXP-0029: learned value policy i certified decision tree były dokładne i osiągnęły D·log2(K) probes, lecz learned używał 8.00% więcej query ops, 41.67% więcej fit, 62.50% więcej policy-build, 19.21% więcej state, 60.19% więcej update i 35.08% więcej workload. Jego update wywołuje `_build()` nad całym codebookiem, więc nie jest lokalny w wymaganym sensie. |
| `nonstationary_online_update_battery_v1` | Jedyny prawdziwie anonimowy prequential boundary: query otrzymuje tylko losowy `slot` i numeric values; target jest ujawniany dopiero update. Mechanism, phase, regime i parametry są niedostępne poza privileged control. | 8/32 | EXP-0043: shared meta-update miał 0.05455 overall, 0.00880 minimum mechanism i zero worst phase; przegrał z independent i LMS oraz płacił 109.73× LMS R16, 59,520× meta-fit i 36.85× state. |

Wspólne nazwy `fit/query/update` nie tworzą wspólnego problemu statystycznego. Pierwszy inventory
zakłada dyskretny DAG, znane candidate-parent sets i ręczną bibliotekę funkcji; drugi zakłada
pełną tabelę etykiet oraz aktywny wybór kolumny; trzeci jest continuous prequential regression
bez action-selection i bez jawnego zbioru hipotez. Generyczny wrapper musiałby dostarczyć osobne
family-specific likelihoods, action semantics, target decoder i hypothesis constructor. To jest
ręczna ontologia niosąca rozwiązanie, nawet gdy wrapper ma jedną nazwę klasy.

## Wynik bramek

| Bramka | Wynik | Powód |
|---|---|---|
| Source-identical observation-only operator | FAIL | Typy outcome, action, target i hypothesis state są niezgodne; lossless common representation nie definiuje wspólnego likelihoodu ani działania. |
| Matched-quality scaling przy ≥3 K | FAIL | Tylko causal inventory ma trzy K, lecz jego dodatnia sygnatura zależy od explicit routing i supplied gate ontology. Active i online mają tylko dwa K. |
| Local update bez global retrainingu | FAIL | Online spełnia boundary, causal update jedynie waliduje już fitted models, a active learned policy globalnie przebudowuje kolejność nad codebookiem. Nie ma jednej wspólnej lokalnej mutacji. |
| OOD reuse odkrytego operatora | FAIL | Causal ponownie używa ręcznie dostarczonych gate primitives; active uczy split order z pełnej labeled table; online shared learned update przegrał causal i classical controls. |
| Strong matched controls | FAIL prospective | Kontrole mają różne zadania i metryki. Złączenie decision tree, Bayes/model bank oraz LMS/RLS/Kalman jako jednego comparatora wymagałoby benchmark-specific dispatch. |

## Interpretacja i niepewność

To jest odrzucenie proponowanego wspólnego testu przed hipotezą, a nie dowód przeciwko całej
rodzinie causal hypothesis competition. Dodatni EXP-0012 pokazuje wąską, realną sygnaturę:
po odkryciu poprawnej dyskretnej struktury wykonanie może pozostać lokalne i K-independent.
Jednocześnie kolejne wyniki pokazują, że acquisition oraz semantyczne routing IDs są kosztowną
częścią problemu, a nie detalem możliwym do pominięcia.

Confidence `0.98`, że obecne trzy immutable inventory nie pozwalają na rzetelny source-identical
test czterech bramek bez nowego kontraktu lub ręcznej ontologii. Niepewność dotyczy przyszłych
naturalnych danych: możliwe, że jeden event interface powstaje tam z obserwowanych perturbacji,
a nie z evaluator-supplied labels.

## Decyzja

`reject_before_hypothesis`. Nie tworzyć HYP-0028 ani EXP-20260831-0006. Nie łączyć trzech
benchmarków adapterami, nie rozszerzać K post hoc, nie reaktywować HYP-0008 lub HYP-0014 i nie
stroić robust causal, learned probe policy ani shared meta-update.

## Następny rozstrzygający krok

Następny wake może wykonać dokładnie jeden no-scoring **natural-intervention inventory audit**
na już istniejących realnych źródłach DS08a, DronePropA i continuous-event. Bez tworzenia
benchmarku lub schematu ma ustalić z frozen metadata/data contracts, czy publiczne obserwacje
zawierają co najmniej trzy anonimowe, powtarzające się perturbacje z pre-intervention support,
post-intervention outcomes i recurrence, które pozwalają wyznaczyć jeden wspólny event tuple
bez nazw rodzin, fault labels, semantic channel names lub oracle segmentation.

PASS wymaga również co najmniej trzech naturalnych skal K, jawnego predict-then-reveal boundary,
lokalnego update counterfactual i możliwości zdefiniowania classical model-bank/RLS oraz
no-update controls bez nowej metryki. Jeśli któregokolwiek elementu brakuje, zapisać
`no_identifiable_natural_intervention_contract` i nie budować kolejnego toy benchmarku. Tylko
pełny PASS może w osobnym późniejszym wake uzasadnić chroniony service design nowej kohorty;
nie zezwala jeszcze na hipotezę ani scoring.

