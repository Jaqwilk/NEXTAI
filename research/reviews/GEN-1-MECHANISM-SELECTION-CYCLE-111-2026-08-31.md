# GEN-1 — selekcja mechanizmu, cykl 111

Zakres: jeden review-only wake po EXP-20260831-0005 i serwisowej migracji raportu do
`heldout_three_family_continuous_transfer_v5`. Nie utworzono hipotezy, planu, seeda,
benchmarku, schematu ani kodu kandydata; scoring nie został uruchomiony. Repozytorium i
audytowany harness NEXTAI pozostają jedynym źródłem oficjalnego evidence. Wyniki z Lab B mogą
jedynie proponować hipotezy i nie zostały użyte jako evidence.

## Obserwacje portfolio

- Stan obejmuje 56 ukończonych eksperymentów, z czego trzy są maszynowo nieważne naukowo.
  Nie ma wyniku `promising`, `promoted` ani dodatniego wyniku oczekującego na replikację.
- Persistence pozostaje powtarzalnie mocnym, stabilnym i tanim punktem odniesienia dla trzech
  rodzin ciągłych. EXP-0005 potwierdził, że zerowy slope kosztu lookupu bez dopasowanej jakości
  nie jest korzystną sygnaturą skalowania.
- Najmocniejszy sygnał ponownego użycia operatora pochodzi z EXP-0057: observable-equation
  propagation osiągnęło 1.0 accuracy we wszystkich komórkach K=32. Ten sam zamrożony learner
  załamał się przy K=8, miał minimum-combination accuracy 0.0 i meta-fit 26.13 razy droższy od
  exact MDL. To próg pokrycia na wspólnym skończonym interfejsie, nie przenośny sukces.
- Najmocniejszy sygnał rozdzielenia wiedzy od query work pochodzi z HYP-0001: analityczne
  indeksowanie stabilnych tożsamości miało zerowy empiryczny slope K. Learned binding w
  EXP-0035 osiągnął tylko 0.5417 cold i 0.5208 near accuracy, zawiódł nowe binding przy K=8 i
  kosztował 2.36 razy więcej workload niż analityczny indeks.
- Doświadczeniowa kompilacja odzyskiwała dokładne opaque codebooks w EXP-0025, lecz learned
  soft unification nie dodało capability ponad exact constraints, było droższe w każdej
  deterministycznej komórce i miało gorszy slope K.

## Porównanie trzech zasad

| Zasada | Naprawialna słabość czy problem fundamentalny? | Trzy wymagane sygnatury | Decyzja |
|---|---|---|---|
| Learned identity binding + sparse local index | Konkretną słabością jest acquisition reprezentacji. Obecny pozytywny wynik zależy jednak od analitycznej stabilności lub supplied positive-pair ontology; istniejący raw benchmark nie rozdziela bez nadania nowej semantyki unsupervised identity acquisition. | K-cost: tylko analityczny control; local update: tak dla indeksu; OOD learned operator reuse: nieobserwowane. | Nie reaktywować HYP-0001 i nie stroić EXP-0035. |
| Permutation-equivariant observable operator equations | Mechanizm relation propagation jest realny, lecz zamrożony test pokazuje fundamentalny low-support identifiability/coverage threshold. Zwiększenie supportu, wybór K=32 albo zmiana relation threshold byłaby post-result tuningiem. | K-cost: trzy jakościowo niedopasowane punkty nie istnieją; local update: tylko deklaratywne; OOD reuse: dodatnie wyłącznie przy K=32, negatywne minimum. | Nie reaktywować HYP-0022 i nie replikować korzystnego K. |
| Validated experience compilation z dependency-local invalidation | Exact symbolic constraints już wyjaśniają capability taniej; learned soft acquisition nie wnosi odrębnej zasady. Reaktywacja wymagałaby zewnętrznego, niezależnego dowodu na non-all-pairs acquisition, którego repozytorium nie ma. | Warm-cost: możliwy klasycznie; local update: możliwy klasycznie; OOD learned reuse i matched-quality trzy-K advantage: brak. | Nie reaktywować HYP-0011 ani additive opaque-alias DSL. |

Przegląd koncentrował się na najbardziej evidence-backed sygnałach oraz ich przyczynach porażki;
nie przeznaczono tego wake na radykalny nowy kierunek. Jest to zgodne z kroczącym, a nie
obowiązkowym-per-wake podziałem 60–70% / 20–30% / około 10%.

## Interpretacja i niepewność

Wspólny wzorzec jest mocniejszy niż pojedyncza porażka implementacji: klasyczne indeksy,
constraints, persistence i lokalne modele uzyskują użyteczne sygnatury wtedy, gdy środowisko
dostarcza właściwą tożsamość lub strukturę. Learned acquisition tej struktury albo przegrywa
jakościowo i kosztowo, albo działa dopiero po przekroczeniu progu pokrycia. To wspiera HYP-0012
o ukrytym koszcie routingu/acquisition, ale nie dowodzi uniwersalnej dolnej granicy.

Niepewność pozostaje wysoka poza lokalnymi, widocznymi quickami: większość wyników ma jeden seed,
a istniejący inventory nie zawiera czystego, lossless observation-only kontraktu, który jednocześnie
testuje trzy skale K, lokalne update i OOD reuse bez supplied ontology. Brak takiego kontraktu nie
jest dowodem, że mechanizm nie istnieje; jest powodem, by nie prerejestrować obecnie nierozstrzygającego
eksperymentu.

## Decyzja

`select_none`. Żadna z trzech zasad nie przechodzi wszystkich wymaganych bramek. Nie tworzyć
HYP-0028, EXP-20260831-0006 ani kolejnego benchmarku. Nie zmieniać ranku, ridge, shrinkage,
bucketów, moments, supportu, relation threshold ani korzystnego zakresu K po wynikach.

Confidence decyzji `select_none`: 0.92 dla obecnego inventory i zamrożonych dokładnych wariantów;
nie jest to confidence 0.92, że żadna przyszła learned architecture nie zadziała.

## Następny rozstrzygający krok

Następny wake może wykonać dokładnie jeden radykalny, no-scoring design gate dla
**observation-only event-driven causal hypothesis competition**. Ma najpierw sprawdzić, czy
istniejące `causal_intervention_adversarial_v2`, `active_information_acquisition_v1` i
`nonstationary_online_update_battery_v1` pozwalają bez zmiany danych lub schematów zdefiniować
jeden source-identical operator, który (a) lokalnie aktualizuje tylko konkurujące hipotezy,
(b) ponownie używa tego samego operatora na niewidzianym mechanizmie oraz (c) daje dopasowaną
jakościowo krzywą pełnego kosztu dla co najmniej trzech K. Obowiązkowe kontrole to certyfikowane
decision tree / entropy-greedy, Bayes/model bank, LMS/RLS/Kalman i no-update stosownie do
istniejących interfejsów.

Jeśli choć jeden z trzech warunków wymaga family labels, ręcznej ontologii, nowego benchmarku,
nowego schematu albo metryki po wyniku, gate ma zapisać `reject_before_hypothesis`. Tylko pełny
PASS może w jeszcze późniejszym wake zezwolić na nową hipotezę i prerejestrację jednego quicka.

