# OBSERVATIONS FROM NEXTAI

Cykl 238 jest wyłącznie ukierunkowaną syntezą literatury względem trzech
niewiadomych zamrożonych w cyklu 237. Nie utworzono hipotezy, planu
eksperymentu, kandydata, benchmarku, schematu ani seeda; nie wykonano
scoringu. Aktywny benchmark pozostaje bez zmian:
`heldout_repository_sequence_compression_v6`.

Podstawą porównania są 94 naukowo ważne ukończone wyniki NEXTAI. Cztery
terminalnie nieważne wyniki i trzy post-seed non-results pozostają historią
diagnostyczną i nie są używane jako evidence. Poniższe obserwacje nie mówią,
że reprezentacje, OOD ani amortyzacja są niemożliwe. Zamrażają dokładnie to,
co powtarzało się pod dotychczasowymi kontraktami.

## U1 — NEXTAI OBSERVATION: identyfikowalność

Anonimowe candidate-visible obserwacje wielokrotnie dopuszczały kilka
behawioralnie zgodnych struktur. Gdy benchmark dostarczał mocny symmetry
breaker — skończony komplet interwencji, stabilne powiązanie obserwacji lub
mały zamknięty język — strukturę zwykle odzyskiwał także exact albo klasyczny
control.

- Niejednoznaczność makr i faktoryzacji: `EXP-20260830-0008/0014`.
- Reprezentacja podana oracle była użyteczna, ale publiczne dane albo koszt
  acquisition jej nie wyznaczały: `EXP-20260830-0020/0025`.
- Operator equations osiągały exact przy K=32, lecz transfer low-support miał
  minimum zero, a meta-fit był droższy od exact MDL: `EXP-20260830-0057`.
- Wspólne reprezentacje zawodziły w programach, operatorach, trzech realnych
  continuous families i czterorodzinnej sparse set memory:
  `EXP-20260830-0041/0042/0048/0050/0052/0056/0057`,
  `EXP-20260831-0001/0002/0003/0005/0008/0009`,
  `EXP-20260901-0038/0057`.
- Source-identical `shared > independent` występowało lokalnie, ale
  `cross-family-only > support-only` nie przechodziło we wszystkich
  rodzinach. To odróżnia regularizację przez pooling od transferu.
- Kontrprzykłady wewnętrzne: `EXP-20260830-0015/0016` odzyskały skończoną,
  identyfikowalną faktoryzację, a `EXP-20260901-0041/0042` nauczyły się małej
  gramatyki i ekstrapolowały głębokość.

Przeżyły sygnatury: reusable operations, depth extrapolation, lokalne
aktualizacje i query work słabo zależny od dormant K. Nie przeżył ogólny,
source-identical most między rodzinami bez dostarczonej ontologii.

## U2 — NEXTAI OBSERVATION: wybór reprezentacji OOD

Development-local fit, likelihood, residual, reconstruction, fitness i
stability często nie wybierały struktury użytecznej na niewidzianym
rolloucie, operacji albo rodzinie. Frozen, shuffled, disabled, one-pass,
single-scale, posterior-mean lub support-only ablation o tym samym źródle i
zbliżonej pojemności bywała równa albo lepsza.

- Routing keys, latent program, update rates i cross-family selection:
  `EXP-20260830-0022/0043`, `EXP-20260901-0007/0011/0013/0017`.
- Future-supervised state, event gating i state/particle selection:
  `EXP-20260901-0024/0029/0060/0062`.
- Learned partitions, bottleneck coordinates, credit traces i addresses:
  `EXP-20260901-0030/0031/0037/0038/0048/0049/0051/0054`.
- Wąskie kontrprzykłady: recurrent residual na WT w
  `EXP-20260831-0006/0007` oraz pushdown w
  `EXP-20260901-0041/0042`. Pierwszy nie przeniósł się family-blind w
  `EXP-20260831-0008`, drugi nie wykonał innej recoverable operation w
  `EXP-20260901-0044`.

Przeżyła sygnatura „learned selector ma mierzalny efekt”, lecz znak efektu
nie był stabilny OOD. Nie przeżyło żadne dotychczasowe uniwersalne frozen
kryterium wyboru.

## U3 — NEXTAI OBSERVATION: amortyzacja pełnego kosztu

Macro discovery, canonicalization, compilation, exact guidance,
certification, learned indexes i kernels zmniejszały query work albo search
nodes, ale acquisition, fit, verification, state, update lub obowiązkowy
input scan kasował zysk względem sufficient statistic, exact algorithm albo
frozen structure.

- Wczesne reuse i macro discovery: `EXP-20260830-0002/0005/0009`.
- Warm prefixes, contraction, persistent macros i compilation:
  `EXP-20260901-0003/0020/0021/0034`.
- Learned exact guidance: `EXP-20260901-0036/0045/0059`.
- Learned index z lokalnym insertion i bounded search:
  `EXP-20260901-0056`.

Przeżyły dokładne warm reuse, local invalidation, malejący warm query cost i
zmniejszenie search nodes. Zwykle korzystały ze stabilnego klucza, ręcznej
normalizacji lub exact fallbacku, a mocny klasyczny control pozostawał tańszy
w granicy full-cost.

# U1 CONTRADICTIONS

## 1. Sufficiently distinct paired views — multi-view nonlinear ICA

Gresele i in. pokazują formalnie, że wspólne niezależne źródła, których nie
da się odzyskać z pojedynczego nieliniowo zmieszanego widoku, stają się
identyfikowalne z dwóch odpowiednio różnych, sparowanych widoków
([SRC-0235](https://proceedings.mlr.press/v115/gresele20a.html)).

- **Co zadziałało / bottleneck:** joint contrast między widokami odwraca
  arbitralne nieliniowe mieszanie do component-wise invertible ambiguity.
- **Dodatkowy sygnał:** jawna para pomiarów tej samej latentnej przyczyny;
  niezależne komponenty, component-wise corruption, invertible mixing i
  techniczny warunek sufficiently distinct views (SDV).
- **Dostęp learnera:** learner widzi, które dwa rekordy są parą; nie dostaje
  nazw czynników.
- **Domenowość / labels / privilege:** brak semantic factor labels i oracle
  latents, ale poprawna korespondencja między modalnościami jest silnym
  relacyjnym nadzorem. W naturalnych sensorach może być obserwowalna; w danych
  konstruowanych przez generator byłaby privileged acquisition.
- **Source-identical:** możliwe jako anonimowy interfejs `paired(view_a,
  view_b)`, o ile wszystkie rodziny naturalnie dostarczają tę samą relację.
- **Koszt:** koszt uzyskania i synchronizacji widoków nie jest rozliczony.
- **Breadth:** twierdzenie jest szerokie względem nonlinear mixing, lecz nie
  pokazuje jednego learnera na niezależnych rodzinach problemów ani
  użyteczności zadaniowej odzyskanych komponentów.

**MISSING INGREDIENT RELATIVE TO NEXTAI:** candidate-visible, sample-level
correspondence dwóch obserwacji tej samej ukrytej przyczyny, przy której
view-specific zakłócenia zmieniają się wystarczająco niezależnie, by rozbić
klasę równoważnych reprezentacji.

## 2. Unknown-target interventions under nonlinear mixing

Buchholz i in. identyfikują latentny linear-Gaussian SCM i graf do skali oraz
permutacji z niesparowanych interventional distributions mimo nieznanych
targetów interwencji i ogólnego injective differentiable nonlinear mixing
([SRC-0236](https://proceedings.neurips.cc/paper_files/paper/2023/hash/8e5de4cb639ef718f44060dc257cb04f-Abstract-Conference.html)).

- **Co zadziałało / bottleneck:** geometryczne kontrasty density-ratio między
  observational i single-node interventional regimes wyznaczają mixing,
  interwencje i strukturę przyczynową.
- **Dodatkowy sygnał:** każdy latentny node musi być objęty co najmniej jedną
  nietrywialną interwencją; dane pozostają pogrupowane według regime; wiadomo,
  który dataset jest observational. Latenty muszą tworzyć linear Gaussian
  SCM, a mixing ma być injective i differentiable.
- **Dostęp learnera:** target IDs i counterfactual pairs nie są widoczne, ale
  granice regime datasets są widoczne.
- **Domenowość / labels / privilege:** brak semantic labels i intervention
  target IDs; kontrola zapewniająca exhaustive single-node coverage jest
  jednak domenowym protokołem. Bez coverage autorzy podają non-identifiability.
- **Source-identical:** anonimowe regime IDs można wyrazić source-identical;
  założenie „jedna interwencja na jeden latentny node” nie jest weryfikowalne
  z samego ogólnego interfejsu.
- **Koszt:** acquisition interwencji nie jest liczony. Autorzy raportują około
  200 CPU-hours i 20 GPU-hours dla wyników oraz około dziesięciokrotnie więcej
  CPU dla preliminaries/hyperparameters.
- **Breadth:** empiryka obejmuje synthetic nonlinear mixtures i renderowane
  obrazy piłek, nie niezależne realne rodziny. Optymalizator ma dodatkową
  lukę: bez mean shifts contrastive method może nie osiągać identyfikowalnego
  rozwiązania mimo twierdzenia.

**MISSING INGREDIENT RELATIVE TO NEXTAI:** wiele rozróżnialnych rozkładów,
które modyfikują pojedyncze ukryte mechanizmy i łącznie pokrywają wszystkie
mechanizmy, nawet jeśli ich nazw nie podano learnerowi.

## 3. Pairwise weak supervision without factor annotations

Locatello i in. uczą disentangled representations z par nie-IID, w których
nieznany podzbiór czynników pozostaje wspólny. Praktyczny learner nie dostaje
nazw grup, czynników ani liczby zmian, a reprezentacje są testowane także na
covariate shift i abstract reasoning
([SRC-0237](https://proceedings.mlr.press/v119/locatello20a.html)).

- **Co zadziałało / bottleneck:** para ogranicza możliwe faktoryzacje przez
  wymuszenie zgodności części kodu, a adaptive averaging szacuje wspólne
  współrzędne bez ich etykiet.
- **Dodatkowy sygnał:** wiadomo, że dwa obrazy współdzielą co najmniej jeden
  czynnik i że zmiany są rzadkie; theorem zakłada independent continuous
  factors, smooth invertible generator, unlimited data oraz znane k.
- **Dostęp learnera:** learner widzi pary, nie factor IDs; praktyka heurystycznie
  estymuje k i shared subset.
- **Domenowość / labels / privilege:** interfejs par nie ma semantyki, ale pięć
  benchmarków tworzy pary za pomocą ground-truth generative factors. Dlatego
  reported acquisition jest privileged względem zwykłych anonimowych danych.
- **Source-identical:** tak na poziomie par, jeśli taka relacja powstaje
  naturalnie; nie, jeśli trzeba ją odtworzyć z ukrytego simulatora.
- **Koszt:** koszt kontroli/generowania par nie jest naliczony; brak porównania
  full-cost z klasyczną faktoryzacją.
- **Breadth:** pięć visual generative datasets to różne dane w jednej klasie
  problemu, nie cross-family learner na programach, dynamice i sekwencjach.

**MISSING INGREDIENT RELATIVE TO NEXTAI:** jawna relacja „te dwa doświadczenia
dzielą tę samą ukrytą sytuację z nielicznymi zmianami”, bez ujawnienia, które
czynniki są wspólne.

# U2 CONTRADICTIONS

## 1. Weakly supervised loss predicts controlled OOD utility

Ten sam wynik Locatello i in. jest kontrprzykładem także dla U2: niższy
weakly-supervised reconstruction loss był ogólnie skorelowany z lepszym
downstream accuracy, a learned representations zachowywały użyteczność pod
kontrolowanym covariate shift.

- **Co zadziałało / bottleneck:** frozen loss jest związany z relacją między
  sparowanymi doświadczeniami, a nie tylko z marginalnym IID reconstruction.
- **Dodatkowy sygnał i dostęp:** learner widzi parę o częściowej stałości;
  downstream/OOD labels nie uczestniczą w samym representation fit.
- **Domenowość / privilege:** testy shift wykorzystują znane generative
  factors, a pary są generowane z ground truth. To silny, lecz privileged
  dowód acquisition; nie dowód na nieznany naturalny cross-family shift.
- **Source-identical / koszt / breadth:** loss może mieć identyczny kod dla
  anonimowych par, ale nie wykazano naturalnego pozyskania par, full cost ani
  jednego niezmienionego modelu poza rodziną visual disentanglement.

**MISSING INGREDIENT RELATIVE TO NEXTAI:** proxy ocenia zgodność pod
obserwowalną zmianą nuisance przy zachowanej części doświadczenia, zamiast
wnioskować OOD utility wyłącznie z fit na jednym rozkładzie.

## 2. Invariant conditional selected across informative environments

Rojas-Carulla i in. zakładają podzbiór cech, dla którego `P(Y|X_S)` pozostaje
stałe między zadaniami, i wybierają go przez testowanie invariance residuals
w wielu znanych środowiskach. Dla domain generalization dowodzą optymalności
w adversarial setting i pokazują wyniki na gene-deletion data
([SRC-0238](https://www.jmlr.org/papers/v19/16-432.html)).

- **Co zadziałało / bottleneck:** środowiska, które zmieniają spurious
  associations, pozwalają odrzucić predyktory o niestabilnych residuals.
- **Dodatkowy sygnał:** supervised Y, environment/task IDs, aligned feature
  identities i założenie, że test zachowuje ten sam conditional. Informative
  interventions zwiększają identyfikowalność causal parents.
- **Dostęp learnera:** training environment IDs i target labels są jawne;
  causal parent labels nie są wymagane przez główny estimator.
- **Domenowość / privilege:** DOMAIN-CONDITIONAL. Gene deletion dostarcza
  rzeczywiste intervention regimes i wspólną przestrzeń genów. Privileged
  causal-parent control istnieje tylko jako oracle comparison i nie jest tu
  evidence dla learnera.
- **Source-identical:** kod testu invariance może być identyczny, ale wymaga
  aligned variables i legalnych environment IDs w każdej rodzinie.
- **Koszt:** koszt interwencji biologicznych i acquisition nie jest liczony;
  nie ma pełnej granicy inference/update/state.
- **Breadth:** synthetic i jeden biological family. Autorzy zaznaczają, że
  testowa invariance assumption jest nietestowalna z training data; kilka
  training-invariant subsets może różnić się na teście.

**MISSING INGREDIENT RELATIVE TO NEXTAI:** kilka oznaczonych training regimes,
w których nuisance mechanisms zmieniają się informacyjnie, podczas gdy ten
sam target conditional pozostaje stabilny.

## 3. Risk extrapolation over known shift directions

REx zamraża kryterium wyrównujące ryzyko między znanymi training domains i
ekstrapoluje poza ich convex hull. W kontrolowanych shiftach i zadaniach RL
potrafi pokonać ERM/IRM
([SRC-0239](https://proceedings.mlr.press/v139/krueger21a.html)).

- **Co zadziałało / bottleneck:** zmiana modelu, która zwiększa różnice ryzyka
  między środowiskami, jest odrzucana jako shift-sensitive.
- **Dodatkowy sygnał:** supervised targets, domain IDs i założenie, że test
  jest silniejszą wersją kierunków variation obecnych w training domains.
- **Dostęp learnera:** wszystkie training-domain losses są jawne; test domain
  nie jest używany do model selection w deklarowanych testach.
- **Domenowość / privilege:** DOMAIN-CONDITIONAL, nie oracle. Kierunek shiftu
  musi być reprezentowany przed testem; homoskedasticity/causal assumptions
  warunkują teorię.
- **Source-identical:** tak dla anonimowych domain IDs i wspólnego supervised
  lossu, ale nie przy braku porównywalnej target semantics.
- **Koszt:** pełny koszt acquisition środowisk i treningu nie jest główną osią
  porównania.
- **Breadth:** Controlled MNIST i zmodyfikowane control tasks pokazują efekt,
  lecz na czterech standardowych DomainBed datasets REx, IRM i ERM są
  porównywalne. Kamath i in. dodatkowo pokazują, że practical IRMv1 może
  przegrać z ERM nawet w population setting
  ([SRC-0240](https://proceedings.mlr.press/v130/kamath21a.html)).

**MISSING INGREDIENT RELATIVE TO NEXTAI:** training domains, których różnice
wyznaczają prawdziwy kierunek przyszłego shiftu, dzięki czemu frozen proxy
może mierzyć wrażliwość na ten kierunek przed OOD.

## 4. Invariance without supplied domain IDs, but with an independent anchor

TIVA uczy environment partition z candidate-visible cech niezależnych od Y,
ale skorelowanych ze spurious features, a następnie stosuje invariance
learning. Theorem i wyniki obejmują synthetic data oraz CelebA, house price i
landcover
([SRC-0241](https://proceedings.mlr.press/v202/tan23b.html)).

- **Co zadziałało / bottleneck:** learner sam wybiera `X_perp` marginalnie
  niezależne od targetu, lecz ujawniające heterogeneity spurious mechanism;
  z nich konstruuje grupy, na których sprawdza invariance.
- **Dodatkowy sygnał:** supervised Y oraz istnienie wystarczającego `X_perp`,
  które jest skorelowane z każdym istotnym spurious feature. Teoria zakłada
  SCM Markov/faithfulness, dostateczną pojemność i separation margins.
- **Dostęp learnera:** raw X i Y; bez environment IDs, causal graph lub
  ręcznie wskazanego anchoru.
- **Domenowość / labels / privilege:** mechanizm jest ontology-light, ale
  CONDITIONALLY dostępny tylko wtedy, gdy taki anchor istnieje. CelebA shift
  jest ręcznie konstruowany, a feature-learning używa pretrained ResNet;
  dlatego ten wynik nie jest zgodny z zakazem zewnętrznego modelu NEXTAI.
- **Source-identical:** formalnie możliwy dla jednego ogólnego `(X,Y)`
  interfejsu; opublikowane eksperymenty zmieniają architekturę, hiperparametry
  i reprezentację między tabular/image/sequence.
- **Koszt:** autorzy raportują GPU runtime i grid search, ale nie pełny koszt
  feature acquisition, pretrained backbone, inference, update i maintenance.
- **Breadth:** trzy modalności, lecz nie jeden niezmieniony learner i nie
  transfer jednej reprezentacji między rodzinami.

**MISSING INGREDIENT RELATIVE TO NEXTAI:** candidate-visible variable, które
nie przewiduje bezpośrednio targetu, ale ujawnia zmiany spurious mechanism i
pozwala zbudować kontrast OOD bez supplied family labels.

# U3 CONTRADICTIONS

## 1. Bourbon: learning admitted only when predicted reuse pays back

Bourbon integruje piecewise-linear learned indexes z production-quality
WiscKey/LSM i przed fit ocenia, czy przewidywane lookup savings przekroczą
learning cost. Na 50 milionach operacji suma obejmuje foreground lookup i
insert, learning oraz compaction
([SRC-0243](https://www.usenix.org/conference/osdi20/presentation/dai)).

- **Co zadziałało / bottleneck:** immutable sorted SSTables są tanimi,
  wielokrotnie używanymi jednostkami fit; exact baseline path zachowuje
  correctness; cost-benefit analyzer pomija krótkowieczne lub często
  przepisywane files.
- **Dodatkowy sygnał:** jawny file lifecycle, sorted-key order, measured model
  construction cost, expected future lookups i compaction behavior.
- **Dostęp learnera:** klucze, file/level boundaries i workload statistics są
  dostępne online; nie ma semantic labels ani oracle answers.
- **Domenowość / privilege:** DOMAIN-CONDITIONAL dla LSM. File immutability,
  scalar key order i exact lookup fallback są częścią ontologii systemu, ale
  nie są ukrytą ground truth.
- **Source-identical:** możliwe dla wielu datasets wewnątrz tego samego
  ordered-key interface; nie dla niepowiązanych rodzin bez narzucenia im
  semantyki key/rank/file.
- **Koszt:** w mixed workload liczono foreground, learning i compaction.
  Aggressive always-learn przy 50% writes zużywało około 134 s na learning i
  miało total time gorszy od WiscKey; CBA zmniejszało learning do około 13.9 s
  przez świadome użycie baseline path. Lookup gains wynosiły 1.23–1.78x, a
  YCSB throughput gains były zależne od workloadu.
- **Breadth:** synthetic i real key distributions oraz wiele YCSB workloads,
  ale jedna rodzina systemowa.

**MISSING INGREDIENT RELATIVE TO NEXTAI:** prospektywnie obserwowalna,
stabilna jednostka reuse z przewidywalnym lifetime oraz admission rule, które
może odmówić learningu zanim poniesie jego koszt i bez utraty correctness
wrócić do exact baseline.

## 2. PGM-index: very cheap fit aligned exactly with the query

PGM-index buduje optymalną piecewise-linear approximation mapy
`ordered key -> rank`, ogranicza błąd do epsilon i domyka lookup lokalnym exact
search. Ma wariant fully dynamic z amortized/worst-case bounds
([SRC-0242](https://www.vldb.org/pvldb/vol13/p1162-ferragina.pdf)).

- **Co zadziałało / bottleneck:** linear-time optimal segmentation daje mały
  state i przewidywalne error window; recursion, update structure i exact
  repair utrzymują matched correctness.
- **Dodatkowy sygnał:** posortowane scalar keys, ich exact ranks, monotonicity
  i publiczny error tolerance. To niemal bezpośrednia sufficient statistic dla
  predecessor/range query.
- **Dostęp learnera:** pełna sorted array i query semantics są jawne; bez
  semantic labels, simulatora i oracle poza exact data structure.
- **Domenowość / privilege:** DOMAIN-CONDITIONAL dla ordered lookup. Nie jest
  privileged w tej domenie, lecz przeniesienie do innych rodzin wnosiłoby
  gotową ontologię adresowania.
- **Source-identical:** tak między key distributions; nie cross-family.
- **Koszt:** construction, query, update i memory są mierzone. PGM zbudował
  index dla 91 GiB/715M pairs w mniej niż 3 s; w reported comparison miał
  podobny lub lepszy czas przy radykalnie mniejszym state niż wybrane trees i
  learned RMI. Koszt powstania samych danych nie jest częścią granicy.
- **Breadth:** real i synthetic distributions do 1B keys, lecz jedna dokładna
  funkcja systemowa.

**MISSING INGREDIENT RELATIVE TO NEXTAI:** discovery jest jednoprzebiegowym,
optymalnym przybliżeniem celu już uporządkowanego przez interfejs, a każdy
błąd ma tanie, lokalne exact repair. To kontrprzykład dla U3, ale zarazem
potwierdzenie NEXTAI RC2: przewaga powstaje na granicy klasycznego algorytmu,
nie z ogólnej learned representation.

# CAUSAL INGREDIENTS

| Causal ingredient | pomaga U1 | pomaga U2 | pomaga U3 | domain-neutral? | dostępny bez ontologii? | full-cost plausible? |
|---|---:|---:|---:|---|---|---|
| Relation-marked experience: wiadomo, które obserwacje dzielą mechanizm, podczas gdy nuisances się zmieniają | tak, rozbija equivalence class | tak, pozwala testować invariance | nie bezpośrednio | interfejs ogólny; poprawność relacji zależy od domeny | tak, jeśli relacja powstaje naturalnie | acquisition zwykle niepoliczony |
| Diverse regimes pokrywające wszystkie latent mechanisms | tak | tak, jeśli target mechanism pozostaje stały | nie | nie; coverage jest domenowym warunkiem | bez nazw targetów tak, bez protokołu nie | koszt interwencji niepoliczony |
| Candidate-visible independent anchor ujawniający spurious heterogeneity | częściowo | tak | nie | formuła ogólna, istnienie warunkowe | tak; nie wymaga nazwy anchoru | nie pokazano pełnej granicy |
| Known training-domain variation reprezentatywna dla test shiftu | częściowo | tak | nie | nie; shift family jest założona | environment IDs nie są ontologią czynników, ale są dodatkową strukturą | acquisition niepoliczony |
| Stabilna jednostka wielokrotnego użycia z obserwowalnym lifetime | nie | nie | tak | zasada ogólna | tak, ale konkretna jednostka bywa domenowa | tak; Bourbon mierzy granicę systemową |
| Tani exact fallback oraz bounded local repair | nie | chroni jakość, nie wybiera reprezentacji | tak | ogólne tylko gdy istnieje verifier | często wymaga znanej semantyki poprawności | tak |
| Cel discovery bezpośrednio zgodny z klasyczną sufficient statistic | rozwiązuje lokalnie, ale usuwa problem | rozwiązuje lokalnie | tak | nie | zwykle nie | bardzo plausible, lecz nie jest nową ogólną zasadą |

# DOMAIN-SPECIFIC VS GENERAL

Klasyfikacja dotyczy ingredientu faktycznie użytego w dowodzie lub empiryce,
nie nazwy algorytmu.

| Przypadek | Klasa | Powód |
|---|---|---|
| Gresele multi-view ICA | `DOMAIN-CONDITIONAL` | anonimowe pairs są ontology-light, ale muszą reprezentować tę samą latentną przyczynę, a view noises spełniać SDV |
| Buchholz intervention CRL | `DOMAIN-CONDITIONAL` | unknown targets nie są potrzebne, lecz single-node regime, full latent coverage i linear-Gaussian SCM są silnym kontraktem |
| Locatello paired disentanglement | `PRIVILEGED` dla reported acquisition; `GENERAL` tylko jako abstrakcyjny pair interface | benchmarkowy generator wie, które czynniki zachowano; naturalne pozyskanie równoważnych par nie zostało wykazane |
| Rojas-Carulla invariant subset | `DOMAIN-CONDITIONAL` | wymaga target labels, aligned variables, environment IDs i testowej stabilności conditional |
| REx | `DOMAIN-CONDITIONAL` | training domains muszą ujawnić kierunek przyszłego shiftu |
| TIVA | `DOMAIN-CONDITIONAL` | nie potrzebuje domain IDs, ale wymaga supervised Y i istniejącego independent anchor; część empirii używa pretrained representation |
| Bourbon | `DOMAIN-CONDITIONAL` | pełny koszt jest realny, lecz sukces opiera się na LSM file lifecycle, sorted keys i baseline path |
| PGM-index | `DOMAIN-CONDITIONAL` | key order, rank target, monotonicity i exact local repair są gotową ontologią query |

Nie znaleziono przypadku `GENERAL`, który empirycznie spełniałby jednocześnie
source-identical, ontology-free, cross-family i full-cost boundary NEXTAI.
Ogólne są dwie abstrakcje interfejsowe — anonimowa relacja między
doświadczeniami i admission based on prospective reuse — ale źródła pokazują
je tylko przy domenowych warunkach poprawności.

# DUPLICATION AGAINST NEXTAI

1. **Paired/contrastive experience nie było całkiem nieobecne.**
   `EXP-20260830-0015/0016` i `EXP-20260901-0041/0042` miały mocny most i
   odzyskały małą strukturę. To nie falsyfikuje Gresele/Locatello: NEXTAI nie
   testował naturalnej sample-level pary tej samej latentnej przyczyny z
   niezależnym view-specific variation w kilku rodzinach. W cross-family
   eksperymentach wspólny tensor/split nie był taką korespondencją.
2. **Interwencje były testowane w mocnej, ale małej formie.** Finite
   intervention libraries i operator equations pozwalały exact/MDL controlom
   odzyskać strukturę. Buchholz nie wnosi więc „interwencji” jako nowej osi;
   wnosi węższy fakt, że regime grouping plus exhaustive latent coverage może
   zastąpić target IDs nawet pod nonlinear mixing.
3. **Invariance proxies były szeroko testowane.** Shared/independent,
   cross-family/support-only, stability, selection i shuffled/frozen ablations
   wielokrotnie zawodziły. Literatura nie przeczy temu bezwarunkowo: jej
   pozytywne wyniki mają informative environments, pair relation albo
   independent anchor. Dotychczasowe NEXTAI families nie gwarantowały żadnego
   z tych trzech warunków. To rozdziela `ingredient absent` od `learner failed`.
4. **Reuse, fallback i koszt nie są nowością dla NEXTAI.** Warm reuse, local
   invalidation, exact guidance i learned indexes już je testowały. Bourbon
   dodaje konkretny brak: przed-fit admission na poziomie jednostki o
   mierzalnym lifetime. PGM dodaje tani optimal fit aligned z query, lecz jest
   dokładnie rodzajem klasycznej sufficient statistic, który RC2 już zamyka
   jako generator ogólnej architektury.
5. **Żaden znaleziony paper nie unieważnia negative mechanisms.** Nie ma
   podstaw do ponownego uruchamiania ani tuningu zakończonych reguł. Źródła
   zmieniają ocenę brakujących warunków danych/systemu, nie wynik istniejących
   kandydatów.

# CROSS-BOTTLENECK CONVERGENCE

Istnieje częściowa, mocna konwergencja U1 i U2:

> **Learner otrzymuje relacyjnie oznaczone doświadczenie, które zachowuje
> mechanizm istotny dla zadania, a niezależnie zmienia mechanizmy nuisance,
> przez co aktywnie rozbija klasy obserwacyjnie równoważnych struktur.**

- Dla U1 relacja między views/regimes/pairs usuwa symetrię, której pojedynczy
  marginal nie może usunąć.
- Dla U2 ta sama relacja tworzy prospektywny test: reprezentacja ma zachować
  predykcję wtedy, gdy zmienia się nuisance, zamiast maksymalizować tylko
  local fit.
- Gresele, Buchholz i Locatello są najbliższym prior art dla identyfikacji;
  Locatello, Rojas-Carulla, REx i TIVA dla wyboru OOD. Różne nazwy sprowadzają
  się do obserwowalnego kontrastu, nie do wspólnej architektury.

U3 nie redukuje się do tego składnika. Po poprawnej identyfikacji i selekcji
potrzebuje oddzielnie stabilnej ekonomicznej jednostki reuse, mierzalnego
lifetime, taniego fallbacku oraz admission rule przed fit. Logiczny łańcuch
jest więc:

```text
relation-marked mechanism variation
    -> identifiable equivalence class (U1)
    -> prospective invariance criterion (U2)
    -> stable reuse unit + pre-fit admission + exact fallback (U3)
    -> possible full-system crossover
```

To nie jest dowód jednego wcześniejszego braku wyjaśniającego wszystkie trzy
bottlenecki. Jest to jeden wspólny missing ingredient dla U1+U2 i osobny
warunek ekonomiczny dla U3.

# WHAT THE LITERATURE DOES NOT SHOW

- Żadne źródło nie pokazuje jednego niezmienionego learnera, który odkrywa tę
  samą użyteczną reprezentację w kilku niepowiązanych rodzinach bez nazw
  rodzin, aligned semantic variables lub domain-specific preprocessing.
- Identyfikowalność theorem nie gwarantuje finite-sample optimization.
  Buchholz raportuje praktyczną zależność od mean shifts; Locatello ma lukę
  między theorem ze znanym k a adaptive heuristic; Gresele odzyskuje tylko do
  określonych transformacji.
- Żaden selector nie gwarantuje utility pod dowolnym unseen shift. U
  Rojas-Carulla testowa invariance assumption jest nietestowalna z training
  data; REx jest słaby poza zgodnym shift family; IRMv1 może zawieść nawet na
  prostych population problems; TIVA wymaga istniejącego anchoru.
- Pełne koszty U1/U2 data acquisition — paired measurements, interwencje,
  labels i kontrola regimes — prawie nigdy nie są częścią Pareto comparison.
- U3 jest przekonująco rozwiązane lokalnie tylko tam, gdzie system już
  dostarcza ordered scalar query, immutable reuse unit i exact fallback.
  PGM/Bourbon nie pokazują przenośnej learned ontology ani cross-family
  capability.
- Żadne źródło nie łączy U1, U2 i U3 w jednym source-identical,
  ontology-free, full-cost efficient systemie.
- Nic w tej syntezie nie jest dowodem następcy LLM, ogólnej inteligencji ani
  nowego scaling law.

# BOTTLENECK STATUS

| Bottleneck | Status | Uzasadnienie | Co pozostaje otwarte dla NEXTAI |
|---|---|---|---|
| U1 identifiability | `CONDITIONALLY-RESOLVED` | Paired sufficiently-distinct views oraz exhaustive unknown-target interventions formalnie usuwają nieidentyfikowalność | naturalna, nieprivileged relacja dostępna w kilku anonimowych rodzinach i reprezentacja użyteczna dla tasku, nie tylko identyfikowalna |
| U2 OOD representation selection | `CONDITIONALLY-RESOLVED` | Pair loss, informative environments, REx i independent anchors wybierają użyteczne reprezentacje pod zgodnym shift family | frozen criterion bez family/domain labels, którego warunki są candidate-visible i które transferuje cross-family |
| U3 full-cost amortization | `CONDITIONALLY-RESOLVED` | Bourbon liczy learning/foreground/compaction i używa admission; PGM liczy fit/query/update/state | pełny crossover poza ordered indexes, bez gotowej query ontology i względem mocnego classical sufficient statistic |

Confidence jest wysokie, że wskazane warunki wystarczają w opisanych domenach,
średnie dla mechanicznej konwergencji U1+U2 i niskie dla przeniesienia jej do
restrykcji NEXTAI. Wszystkie trzy ścisłe pytania NEXTAI pozostają nierozwiązane
mimo lokalnego `CONDITIONALLY-RESOLVED`.

# BELIEF-CHANGING QUESTION

**Pytanie główne:**

> Czy candidate-visible, anonimowa relacja między doświadczeniami, która
> gwarantuje zachowanie target-relevant mechanism przy niezależnej zmianie
> nuisance mechanisms, jest wystarczająca do identyfikacji i prospektywnego
> wyboru jednego transferable quotient w kilku niewidzianych rodzinach, bez
> factor/family labels, intervention-target IDs, simulatora, external modelu
> lub target-shaped preprocessingu i po naliczeniu kosztu pozyskania tej
> relacji?

**Pytanie alternatywne:**

> Czy po niezależnym uzyskaniu poprawnej struktury candidate-visible sygnał
> przyszłego reuse/lifetime wraz z pre-fit admission i exact fallbackiem jest
> wystarczający, aby pełny koszt acquisition, fit, verification, state,
> update i query przeszedł poniżej najmocniejszego klasycznego controlu bez
> narzucenia semantic key/rank ontology?

# DECISION

**A — częściowy wspólny missing ingredient.** Ten sam mechaniczny składnik —
relation-marked variation rozbijające obserwacyjne equivalence classes — jest
niezależnym warunkiem sukcesu dla U1 i U2. U3 wymaga odrębnego warunku
ekonomicznego: stabilnej jednostki reuse oraz odmowy learningu przed kosztem,
gdy break-even nie jest wiarygodny.

Literatura obniża confidence w wyjaśnienie „same learners są po prostu za
słabe” i podnosi confidence w wyjaśnienie „dotychczasowe anonymous marginals
nie zawierały właściwego relacyjnego symmetry breakera”. Nie dostarcza jednak
legalnego, naturalnego źródła tej relacji dla wielu rodzin ani wspólnego
rozwiązania full-cost.

Nie utworzono eksperymentu ani immutable planu (`experiment_id: none`,
`plan_path: none`). Decyzja nie zmienia statusu żadnej hipotezy, nie promuje
mechanizmu i nie autoryzuje scoringu. Następnym dopuszczalnym krokiem jest
osobna decyzja, czy pytanie główne ma wystarczający naturalny i nieprivileged
observable, aby dopiero później mogło zostać prerejestrowane jako experiment
99; ten cykl nie projektuje tego eksperymentu.
