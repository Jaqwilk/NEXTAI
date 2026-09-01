# OBSERVATION

Cykl 239 jest wyłącznie service/review-only. Nie utworzono formalnej hipotezy
`HYP-*`, planu eksperymentu, evaluatora, benchmarku, schematu, kandydata ani
seeda; nie wygenerowano danych i nie wykonano scoringu. Aktywny benchmark
pozostaje `heldout_repository_sequence_compression_v6`.

Dokładna teza nie jest duplikatem dotychczasowego NEXTAI. W
`EXP-20260901-0054/0056` poprawne pary, pary przetasowane i frozen encoder były
częścią konkretnego learned-address/router systemu; representation learning,
routing i koszt dostępu zmieniały się razem, a raw nearest-neighbour/k-d tree
wygrywały. W `EXP-20260901-0003` dodatnie pary oznaczały exact-equivalent
re-encodings operatora, więc relacja była skonstruowana z task output semantics;
`independent` i `no_pairing` dorównały pełnemu learnerowi, a exact interpreter
go zdominował. Są to silne ostrzeżenia i obowiązkowe prior controls, lecz nie
test identycznych obserwacji oraz identycznego learnera różniących się wyłącznie
jakością neutralnej relacji pod niezależnym nuisance OOD.

Najbliższy wcześniej audytowany realny zbiór, Light Tunnel CRL, nie spełnił
łącznie bram: oficjalnego unseen-world splitu, trzech wspólnych skal i jednego
source-identical interface bez znanej grupy causalnej. Nie pobrano go i nie
otwarto outcome'ów. Dlatego kontrakt poniżej używa małego, neutralnego procesu
powtórnego pomiaru. Nie jest on dowodem na naturalne dane ani cross-family
zasadę; jego jedynym celem jest tani falsifying screen.

# BRIDGE HYPOTHESIS

Zamrożona hipoteza `BRIDGE-U1-U2-V1` brzmi dokładnie:

> A source-identical learner can recover and select an OOD-useful latent
> structure from otherwise ambiguous observations when its experience contains
> ontology-free relational information linking observations that preserve
> task-relevant mechanism while varying nuisance factors. Destroying that
> relational structure while keeping the observations fixed should destroy the
> OOD advantage.

To nie jest przyjęte twierdzenie ani zmiana confidence. Jest to kontrakt do
próby falsyfikacji. U3 i amortyzacja pełnego kosztu nie są hipotezą tego cyklu.

# CAUSAL QUESTION

Czy przy dokładnie tym samym uporządkowanym multizecie rekordów, targetów,
budżecie, kodzie, pojemności i output contract poprawne anonimowe krawędzie
powtórnego pomiaru powodują OOD improvement, którego nie ma po ich derangement,
zastąpieniu niezależnym matchingiem albo usunięciu?

Jedyną dozwoloną zmienną przyczynową jest tablica relacji treningowych. Relacje
nie są dostępne podczas single-record IID/OOD query. To wyklucza wyjaśnienie,
że wynik pochodzi jedynie z łączenia dwóch rekordów w czasie inference.

# LEGAL RELATIONAL SIGNAL

Provisional contract ID, zarezerwowany wyłącznie w tym raporcie, to
`anonymous_repeated_measurement_ood_v1`. Nie jest aktywną kohortą.

Neutralny instrument generuje zdarzenie `i` przez wylosowanie źródła
`z_i in {-1,+1}^16`, po czym wykonuje dokładnie dwa powtórne pomiary. Krawędź
między numerami dwóch pomiarów powstaje z zegara/acquisition counter przed
losowaniem zapytań, korupcji i targetów. Kandydat otrzymuje wyłącznie parę
indeksów; nie otrzymuje `i`, `z_i` ani typu zmiany.

Dla każdego końca pary niezależnie losowane jest `q in {-1,+1}^16`. Target
evaluatora to `y=(z_i^T q)/16`. Rozkład `y` jest taki sam dla każdego `z_i`, a
dwa targety w poprawnej parze są niezależne, ponieważ ich `q` są niezależne.
Sama krawędź nie ujawnia więc ani wartości, ani równości targetu. Konstruktor
relacji nie ma dostępu do `q`, `y` ani nuisance.

Candidate-visible pomiar ma postać `m = b * z_i + epsilon`, współrzędna po
współrzędnej, gdzie `b` jest maską Bernoulliego, a `epsilon` niezależnym
szumem Gaussa. Rekord jest płaskim wektorem długości 32 złożonym z `m` i `q`,
po czym współrzędne przechodzą publiczną permutację bit-reversal pięciu bitów:
`pi(j)=reverse_5_bits(j)` dla `j=0..31`. Interfejs nie nadaje nazw obu częściom.
Wszystkie role widzą bitowo identyczne rekordy i targety.

# ONTOLOGY FIREWALL

Candidate-visible są tylko: płaski `float[32]`, treningowy skalar targetu,
tablica par indeksów lub jej brak oraz zwykłe granice fit/query. Zabronione są:
family/task names, semantic column names, event/object IDs, `z`, maska `b`,
poziom lub typ nuisance, latent coordinates, causal graph, intervention target,
ground-truth correspondence poza anonimową krawędzią, target formula,
simulator state, ręczne invariant/nuisance oznaczenia i adapter per rola,
rodzina albo endpoint.

Kod kandydata nie może rozcinać wektora według ukrytej roli `m/q`, odwracać
znanej permutacji na podstawie evaluator knowledge ani używać stałych z
generatora. Jedna implementacja i jeden zestaw stałych muszą obsługiwać każdą
rolę i wszystkie skale. Mechaniczne source audit odrzuca nazwy/importe
generatora oraz odczyt evaluator-only artifacts.

# PROPOSED CONTRACT

- Stały wymiar źródła i zapytania: 16; candidate input: anonimowy `float[32]`.
- Trzy skale acquisition: `K=64,256,1024` źródłowych zdarzeń; dokładnie dwa
  rekordy na zdarzenie, czyli `2K` rekordów treningowych.
- Train nuisance zawiera wyłącznie pojedyncze korupcje: Gaussian-only
  `(sigma,p)=(1/16,0)` albo `(1/8,0)` oraz erasure-only `(0,1/16)` albo
  `(0,1/8)`. Dwa końce pary losują korupcję niezależnie. Kombinacja obu
  nuisance nie występuje podczas fit.
- IID test używa nowych `z,q` i tego samego zbioru czterech pojedynczych
  korupcji. Każdy OOD cell używa nowych `z,q`, tego samego target mechanism i
  połączonej korupcji; nie zmienia task-relevant distribution.
- Dla każdego K i każdego z czterech test conditions evaluator tworzy 256
  niezależnych zdarzeń query. Dokładnie te same test records są współdzielone
  przez wszystkie role.
- Relacja jest dostępna wyłącznie podczas fit. Każde query jest jednym rekordem
  bez event ID, partnera ani relation edge.
- Przyszły plan musi zamrozić jeden learner przed candidate implementation.
  Wrapper musi mieć `fit(records, targets, relation_edges, relation_mask)`,
  `represent(record)` oraz `predict(record)`. Predykcja musi korzystać z tej
  samej reprezentacji, którą mierzy evaluator; niedozwolony jest ukryty raw
  bypass. Wymiar, optimizer i wszystkie stałe zostaną prerejestrowane przed
  kodem, ale nie są wybierane w tym review-only cyklu.
- Wszystkie learned roles wykonują identyczną liczbę minibatchy i kroków.
  Dla PASSIVE ten sam relation branch wykonuje maskowany no-op i jego koszt jest
  naliczany; nie wolno użyć osobnej ścieżki/modelu.
- Runner-random seed policy i realizacja seeda należą dopiero do późniejszego
  planu. W tym cyklu nie określono ani nie pobrano żadnego seeda.

Ten mechaniczny generator przechodzi dziesięć bram kontraktu: relacja wynika z
powtórnego pomiaru, nuisance OOD jest osobne od target mechanism, role różnią
się tylko krawędziami, istnieją trzy skale, klasyczne metody mają ten sam input,
leakage jest audytowalne, nie ma family logic, a dokładne znaczenie anonimowej
relacji może zostać później powtórzone w innej rodzinie.

# ROLE DEFINITIONS

- `CORRECT_RELATION`: matching `[(2i,2i+1)]` sprzed ukrycia kolejności rekordów.
- `SHUFFLED_RELATION`: te same `K` slotów i stopnie; prawy endpoint przechodzi
  runner-seed-derived derangement bez fixed points i bez prawdziwej pary.
- `PASSIVE`: identyczne rekordy, targety, kroki i kod; relation mask jest w
  całości fałszywa, a krawędzie nie dostarczają gradientu.
- `RANDOM_RELATION`: niezależny uniform perfect matching wszystkich `2K`
  rekordów, bez self-edge i bez prawdziwych par; edge count i degree są takie
  same jak w CORRECT_RELATION.
- `STRONG_CLASSICAL_CONTROL`: predeclared implementable classical envelope na
  legalnym input boundary i poprawnych anonimowych krawędziach, opisany niżej.
- `ORACLE`: evaluator-only predykcja z niezakłóconych `z,q`; mierzy sufit i nie
  jest kandydatem, evidence ani źródłem train signal.

Globalne ukrycie kolejności rekordów następuje po utworzeniu wszystkich czterech
tablic relacji i jest identyczne dla ról. Każda learned role wskazuje ten sam
candidate hash; gate odrzuca różny hash, capacity, batch order albo budget.

# STRONG CONTROLS

Klasyczny envelope musi zawierać co najmniej trzy prerejestrowane implementacje
bez dodatkowej ontologii:

1. degree-2 polynomial ridge na anonimowym płaskim wejściu bez relacji;
2. linear CCA na endpointach poprawnych par, po którym następuje ten sam
   degree-2 ridge na reprezentacji plus publicznym płaskim wejściu;
3. degree-2 kernel CCA/ridge wykorzystujące wyłącznie rekordy, targety i
   poprawne krawędzie.

Wszystkie regularizacje, rank i numeryczne tolerancje muszą zostać ustalone
analitycznie albo na osobnym development-only fixture przed scoringiem. Nie
wolno wybierać kontroli po OOD. Raport pokazuje każdą kontrolę; dla kill gate
używany jest ich najniekorzystniejszy dla kandydata implementowalny Pareto
envelope. PCA/ICA i nearest-neighbour mogą zostać dodane tylko przed planem,
jeżeli pre-seed redundancy audit pokaże, że są mocniejsze na tym samym boundary;
po wyniku zestaw jest zamknięty.

# OOD SPLIT

OOD jest zamrożone jako trzy niewidziane połączone korupcje:

- `S1: (sigma,p)=(3/16,3/16)`;
- `S2: (sigma,p)=(1/4,1/4)`;
- `S3: (sigma,p)=(3/8,3/8)`.

Każdy poziom zmienia równocześnie tylko dwa z góry zdefiniowane nuisance
mechanisms. `z`, `q`, target formula, wymiar, liczba query i output contract są
niezmienne. Main evidence pochodzi z S1-S3; IID jest diagnostyką. Zabronione są
random IID split jako main result, wybór shiftu po danych i usuwanie trudnego
cellu. Minimum-cell oznacza maksimum NRMSE po pełnym iloczynie K x S.

# METRICS

- IID oraz każdy OOD-cell: `NRMSE = RMSE/std(y)`; mniej jest lepiej.
- `minimum-cell OOD quality` jest raportowane jako worst-cell NRMSE.
- Gapy mają znak dodatni na korzyść correct:
  `NRMSE(role)-NRMSE(CORRECT_RELATION)` dla shuffled, passive, random i każdej
  klasycznej kontroli.
- Degradation slope: OLS slope NRMSE względem indeksu severity `0,1,2,3`, z
  IID jako zero; raportowane są trzy K-specific slopes i ich różnice.
- Representation stability bez latent access: na evaluator-only powtórnych
  pomiarach obliczany jest median squared distance prawdziwych par podzielony
  przez median distance degree-matched broken pairs. Raport obejmuje też
  coordinate variance i odrzuca collapsed/undefined representation.
- Dla paired significance używane są per-query squared-error differences i
  paired normal intervals; rodzina 27 testów (3 kontrasty x 3 skale x 3 OOD
  severities) podlega Holm-Bonferroni przy family-wise alpha 0.05. To nie jest
  seed replication.
- Pełny koszt od początku: acquisition ops/bytes, relation construction lub
  synchronisation cost, preprocessing ops, fit ops, query ops, update ops,
  state bytes, peak bytes, bytes touched, wall time jako diagnostyka oraz
  workload R1/R4/R16. Koszt ORACLE nie wchodzi do Pareto.

# PRIMARY PREDICTION

`BRIDGE-U1-U2-V1` otrzymuje wyłącznie screening support, gdy cała poniższa
koniunkcja przechodzi:

1. We wszystkich trzech K średni OOD NRMSE correct jest co najmniej `0.05`
   absolutnie i `10%` względnie niższy niż passive.
2. Ten sam próg przechodzi przeciw shuffled.
3. Ten sam próg przechodzi przeciw random.
4. Każdy z 27 paired loss contrasts jest dodatni po Holm-Bonferroni.
5. W każdym K gap do każdego negatywnego role pozostaje dodatni na S1-S3, a
   gap na S3 jest co najmniej `0.8` odpowiedniego gapu na S1.
6. K=64,256,1024 przechodzą; uśrednienie nie może ukryć failed scale/cell.
7. Correct ma finite worst-cell NRMSE `<=0.75`, niecollapsed representation i
   lepszy relation-stability ratio niż każda source-identical ablation.
8. Żadna implementowalna klasyczna kontrola nie ma NRMSE w granicy `0.01`
   correct przy nie większym acquisition, fit, query, workload, state i peak
   cost; correct pozostaje na implementowalnym Pareto frontier.
9. OOD conjunction przechodzi niezależnie od IID; sama poprawa IID, training
   loss albo representation consistency nie jest support.
10. Hash, code path, capacity, budget, records, targets i test queries są
    source-identical, a jedyną różnicą learned roles jest relation table/mask.

Próg `0.05/10%`, tolerancja `0.01`, limit NRMSE `0.75` i retencja gapu `0.8`
są data-free screening constants zamrożonymi teraz. Nie wolno ich kalibrować na
wygenerowanych danych. Jeden pozytywny quick nie zmienia confidence, statusu na
promising/promoted ani nie uruchamia automatycznie replikacji.

# KILL CRITERIA

Jedno z poniższych kończy dokładny claim bez rescue tuningu:

- correct nie przechodzi któregokolwiek kontrastu/scale/cellu powyżej;
- shuffled albo passive są w granicy progów correct;
- random relation jest w granicy progów correct;
- implementowalny classical envelope dorównuje/lepiej działa przy równym lub
  niższym pełnym koszcie;
- leakage audit, source identity, hash, matched records albo target-independence
  relation constructor nie przechodzą;
- efekt znika już na S1, spada o więcej niż 20% do S3 albo istnieje tylko IID;
- target można przewidzieć z samej relacji lepiej niż z jego znanego
  symetrycznego rozkładu;
- potrzebne jest dzielenie według ukrytych części wejścia, family-specific
  preprocessing, event ID, nuisance type albo generator state;
- efekt istnieje tylko w jednej/dwóch skalach;
- ORACLE osiąga finite NRMSE bliskie zero, lecz legalny learner nie wykorzystuje
  poprawnej relacji zgodnie z pełną koniunkcją.

Po kill nie wolno zmieniać thresholdów, lossu, model size, supervision,
korupcji, skali, targetu ani benchmarku pod tym samym claimem. Dokładny learner
zostaje zamknięty; raport pozostaje historią negatywną.

# ADVERSARIAL CHECKS

Przyszły plan musi prerejestrować i wykonać:

1. relation derangement (SHUFFLED_RELATION);
2. pair breaking niezależnie potwierdzający brak prawdziwych edges;
3. identyczną dla train/test i wszystkich ról permutację
   `pi_adv(j)=(7j+3) mod 32`, bez zmiany kodu/hyperparameters;
4. wzrost nuisance S1-S3;
5. niewidziane Gaussian-plus-erasure combinations;
6. byte-identical record/target multiset i równe data volume;
7. jeden candidate bundle hash dla czterech learned roles;
8. static/runtime leakage audit konstruktora relacji i candidate imports;
9. RANDOM_RELATION jako całkowicie nieistotny, degree-matched signal.

Pre-seed fixture musi dodatkowo wykazać, że umyślnie podstawiony learner
odczytujący event order, ukryty split `m/q` albo target buffer zostaje odrzucony
przed scoringiem.

# CROSS-FAMILY PROMOTION RULE

Nawet pełny pozytyw jednej rodziny jest tylko quick-screenem. Przed dowolnym
general-principle, promising, promotion albo wzrostem confidence wymagane są
niezmienione causal role semantics i jeden niezmieniony learner w
jakościowo innej rodzinie, minimum trzy runner-random seeds oraz z góry
zamrożony adversarial operation.

Znaczenie relacji pozostaje dokładnie: „dwa anonimowe pomiary powstały w jednym
neutralnym acquisition event i zachowują task-relevant source, podczas gdy ich
surface disturbance jest losowane niezależnie”. Nie wolno po pozytywie zmienić
go na semantic equivalence, tę samą klasę, ten sam object ID, output agreement
ani dowolne domain labels. Druga rodzina nie jest tutaj wybierana ani
projektowana.

# INTEGRITY RISKS

- Generator syntetyczny może zawyżać dostępność zsynchronizowanych pomiarów.
  Dlatego nawet pozytyw nie świadczy o naturalnej acquisition ani cross-family
  dostępności; koszt synchronizacji jest obowiązkowy.
- Powtórzenie `z` jest legalne tylko dlatego, że edge powstaje z mechanicznego
  acquisition counter. Jeżeli implementacja potrzebuje wyszukać równość
  latentów lub targetów po ich wygenerowaniu, kontrakt staje się privileged i
  musi zostać unieważniony przed seedem.
- Bilinear target daje degree-2 ridge realną szansę całkowicie wyjaśnić efekt.
  To zamierzone: benchmark nie chroni proponowanego learnera przed klasycznym
  zwycięstwem.
- Parametry learnera nie są zamrożone w tym cyklu, bo ich wybór byłby
  architekturą. Następny plan musi je prerejestrować przed kodem i bez oglądania
  jakichkolwiek danych z tego generatora. Brak takiej precommitment kończy próbę
  przed seedem.
- Nie wolno modyfikować aktywnego evaluatora/manifestu ani reinterpretować
  wcześniejszych wyników. Ewentualny przyszły evaluator jest nową kohortą v1 i
  wymaga service integrity/preflight przed planem.
- Jeden runner seed nie estymuje seed variance. Holm intervals wykorzystują
  query heterogeneity, nie replikacje, i nie uprawniają do promotion.

# DECISION

`A. FREEZE_CONTRACT`.

Zamrożono `BRIDGE-U1-U2-V1`, observation boundary, jedyną zmienną przyczynową,
role, neutralny generator, trzy skale, OOD split, metrics, primary conjunction,
kill criteria, klasyczne kontrole, adversarial checks, ontology firewall i
cross-family promotion rule. Kontrakt jest mechanicznie audytowalny, a
relation-only target leakage jest wykluczone konstrukcyjnie przez niezależne
`q` i stały rozkład `y` dla każdego źródła.

Nie utworzono planu ani eksperymentu 99. Następny dozwolony cykl może najpierw
utworzyć nową chronioną kohortę/evaluator zgodnie dokładnie z tym raportem,
wykonać fixtures, preflight, integrity i doctor, a następnie — tylko jeśli
prerejestracja nastąpi przed candidate implementation i seedem — uruchomić
jeden tani quick. Jeżeli runner wymaga osobnego protected service migration,
ten następny cykl pozostaje no-scoring; nie wolno omijać tej granicy.

Końcowa walidacja cyklu: pełne `617` testów przeszło, integrity zweryfikowało
`796` chronionych plików bez problemu, a doctor zakończył się `PASS`. Nie
zmieniono chronionego evaluatora, manifestu, runnera, schematu ani kandydata.
