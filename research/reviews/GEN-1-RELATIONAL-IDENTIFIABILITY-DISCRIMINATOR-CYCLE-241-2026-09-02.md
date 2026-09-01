# OBSERVATION FROM CYCLE 240

Cykl 240 prawidłowo zatrzymał `anonymous_repeated_measurement_ood_v1` przed
scoringiem. Wszystkie bramki integralności przeszły, ale relation-free
degree-2 ridge osiągnął na K=1024 NRMSE `0.522/0.538/0.653` dla S1/S2/S3,
poniżej zamrożonego sufitu `0.75`. Było to `P3`: prosta kontrolka pasywna
rozwiązywała użyteczną część zadania. Nie powstał learned result ani evidence.

Cykl 241 jest wyłącznie review/design. Nie utworzono kandydata, evaluatora,
hipotezy, planu, runner-random seeda ani `EXP-99`; nie wykonano scoringu.
Historyczny v1 pozostaje niezmieniony w stanie `maintenance`.

# WHY V1 FAILED AS A DISCRIMINATOR

V1 nie miał certyfikatu dwóch światów, które są identyczne dla wszystkich
legalnych danych pasywnych, lecz wymagają przeciwnych rozszerzeń OOD. Target
był jawną funkcją stopnia drugiego pojedynczego rekordu. Relacja mogła więc
poprawiać finite-sample estimation, ale nie była jedynym sygnałem wybierającym
jedną z obserwacyjnie równoważnych reprezentacji.

Zmiana progu, większy shift, inny ridge albo nowa nuisance schedule nie
naprawiłaby tej wady. Potrzebny jest inny kontrakt obserwacji: PASSIVE ma być
nieidentyfikowalny nawet przy nieskończonych danych, a CORRECT ma rozbijać
dokładnie wskazaną symetrię.

# IDENTIFIABILITY REQUIREMENT

Kontrakt jest dopuszczalny tylko wtedy, gdy spełnia łącznie:

1. Istnieją dwa światy `W` i `W_swap` o dokładnie tym samym rozkładzie całego
   legalnego pasywnego transcriptu: rekordów, targetów train/IID, masek,
   liczności i kolejności.
2. Istnieją reprezentacje H1 i H2 o identycznym, wysokim train/IID score;
   różnica nie może wynikać z niedouczenia lub małej próbki.
3. H1 i H2 mają analitycznie różny OOD risk, a poprawna odpowiedź zamienia się
   między `W` i `W_swap`.
4. Jedyną candidate-visible różnicą zdolną wybrać poprawną stronę jest
   anonimowa relacja między rekordami.
5. SHUFFLED, RANDOM i PASSIVE zachowują identyczne obserwacje, targety, kod,
   pojemność i budżet, ale nie zawierają tego symmetry breakera.
6. Relacja nie zawiera targetu, klasy, nazwy czynnika, współrzędnych latentnych,
   environment ID ani ręcznej ontologii.
7. Istnieje mocny klasyczny relation-aware control. Jeśli rozwiązuje zadanie
   taniej, learned mechanism przegrywa; nie wolno osłabiać controlu.
8. Skala oznacza liczbę niezależnych fizycznych źródeł/powtórzeń, nie rozmiar
   sztucznie napompowanego tensora.

# CANDIDATE CONTRACTS

Rozważono trzy strukturalnie różne kontrakty, bez projektowania architektury.

**C1 — orthogonal double-matching source swap (`RID-CONTRACT-001`).** Dla
`d=16` evaluator-private `[A B D]` jest macierzą ortogonalną w `R^(3d)`. Płaski
rekord ma postać

`x = A s + B n + D q`,

gdzie `s,n` są niezależne i jednostajnie rozłożone na sferze o promieniu
`sqrt(d)`, a `q ~ N(0,I)`. Labeled train/IID ma `n=s` i
`y=q^T s/sqrt(d)`. Auxiliary pool ma `2K` anonimowych rekordów oraz dwa
ukryte, losowane symetrycznie i edge-disjoint perfect matchings: `M_s` dzieli
`s`, a `M_n` dzieli `n`. PASSIVE nie widzi żadnego z nich. CORRECT ujawnia
wyłącznie krawędzie `M_s`. Naturalne skale to K=`64/256/1024` niezależnych
źródeł; formuła i `d` nie zmieniają się między skalami.

**C2 — finite-field double-matching swap.** Ten sam certyfikat można zbudować
w `GF(2)`: płaski bit-vector jest nieznanym odwracalnym mieszaniem `(s,n,q)`,
train ma `n=s`, a target jest parytetem `q^T s`. CORRECT wskazuje matching
wspólnego `s`; klasyczna eliminacja Gaussa odzyskuje właściwą dual subspace.

**C3 — anonymous cross-view frame alignment.** Dwa isotropic views mają
nieznane układy współrzędnych `U` i `V`. Pasywne, niesparowane marginesy nie
wyznaczają względnego obrotu. Same-state cross-view pairs wyznaczają go przez
Procrustes/cross-covariance, a OOD wymaga transferu predyktora z jednego view
do drugiego.

# H1/H2 AMBIGUITY CERTIFICATES

## C1 certificate

1. **H1:** `rho_s(x)=(A^T x,D^T x)=(s,q)` i
   `h_s(x)=q^T s/sqrt(d)`.
2. **H2:** `rho_n(x)=(B^T x,D^T x)=(n,q)` i
   `h_n(x)=q^T n/sqrt(d)`.
3. **Oba fitują passive train:** na train/IID `n=s`, więc `h_s=h_n=y`
   punkt po punkcie; population NRMSE obu wynosi 0.
4. **PASSIVE nie rozróżnia:** labeled transcript jest niezmienny po
   `A<->B`. W auxiliary transcript oba ukryte matchings i oba rozkłady
   latentów są identyczne; po całkowaniu po ukrytych `M_s,M_n` zamiana
   `(A,M_s,s)<->(B,M_n,n)` nie zmienia prawa żadnego widocznego rekordu.
5. **Co rozbija relacja:** dla krawędzi CORRECT
   `E[x_i x_j^T | (i,j) in M_s]=A A^T`, więc relacja wskazuje stabilną
   subspace bez podawania jej bazy lub nazwy.
6. **Dlaczego SHUFFLED nie rozbija:** degree-matched krawędzie wykluczające
   `M_s` i `M_n` łączą niezależne `s,n,q`, więc population cross-covariance
   wynosi 0. PASSIVE nie ma aktywnych krawędzi.
7. **Dlaczego OOD się różni:** przy niezależnych `s,n` H1 ma NRMSE 0, H2
   `sqrt(2)`, a symetryczny extension `(h_s+h_n)/2` ma `1/sqrt(2)`.
8. **Dlaczego relacja nie koduje targetu:** matching jest konstruowany przed
   `q` i targetem, auxiliary endpoints są unlabeled, a dla niezależnych
   `q_i,q_j` hipotetyczne targety poprawnej pary są dokładnie niezależnymi
   `N(0,1)`, tak samo jak dla null pair.

## C2 certificate

1. **H1:** decode pierwszą latentną subspace i licz
   `(-1)^(q^T s)`.
2. **H2:** decode drugą latentną subspace i licz
   `(-1)^(q^T n)`.
3. **Oba fitują passive train:** `n=s`, więc accuracy obu wynosi 1.
4. **PASSIVE nie rozróżnia:** odwracalne mieszanie oraz dwa symetryczne ukryte
   matchings są niezmienne w prawie po zamianie `s<->n`.
5. **Co rozbija relacja:** XOR różnic poprawnych par nie zawiera składowej
   `s`; jego nullspace identyfikuje dual stable subspace.
6. **Dlaczego SHUFFLED nie rozbija:** różnice null pairs rozpinają wszystkie
   trzy bloki i nie zostawiają wyróżnionej `d`-wymiarowej nullspace.
7. **Dlaczego OOD się różni:** H1 pozostaje exact; dla niezależnych niezerowych
   `s,n` błąd H2 wynosi dokładnie
   `(1-1/(2^d-1))/2` przy jednostajnym `q`.
8. **Dlaczego relacja nie koduje targetu:** matching powstaje przed `q`, a
   niezależne probes czynią parytety endpoints jednostajnymi i niezależnymi.

## C3 certificate

1. **H1:** prawdziwe wyrównanie views `R=V U^T`.
2. **H2:** alternatywne `R_Q=V Q U^T` dla niebanalnego orthogonal `Q`.
3. **Oba fitują passive train:** labeled training odbywa się tylko w pierwszym
   view, więc względne wyrównanie nie wpływa na jego risk.
4. **PASSIVE nie rozróżnia:** isotropic unpaired marginals drugiego view są
   identyczne dla każdego `Q`.
5. **Co rozbija relacja:** same-state cross-view pairs mają cross-covariance
   proporcjonalną do `V U^T`.
6. **Dlaczego SHUFFLED nie rozbija:** niezależne cross-view pairs mają zerową
   cross-covariance.
7. **Dlaczego OOD się różni:** transfer targetu do drugiego view jest exact dla
   H1; np. `Q=-I` odwraca przewidywanie H2 i daje dodatni gap.
8. **Dlaczego relacja nie koduje targetu:** endpoints są unlabeled, pairing
   powstaje przed niezależnym probe/targetem i ujawnia tylko korespondencję.

# PASSIVE TRAIN/IID EQUIVALENCE

C1 ma najsilniejszy certyfikat. Dwa matchingi sprawiają, że flat auxiliary
pool może nawet ujawnić istnienie dwóch powtarzalnych subspaces, ale bez
relacji nie może nazwać żadnej jako `s`: pełny transcript ma automorfizm
zamieniający je miejscami. Labeled support `n=s` leży dokładnie na zbiorze,
na którym H1 i H2 są tą samą funkcją. To population non-identifiability, nie
brak mocy statystycznej.

W przyszłym evaluatorze równoważność musiałaby być sprawdzana przez paired
twin-world fixtures: po zamianie `A/B`, `M_s/M_n` i tych samych publicznych
rekordów wszystkie PASSIVE hashes oraz wszystkie train/IID predictions muszą
być identyczne. Jakakolwiek pasywna cecha wybierająca H1 odrzuca kontrakt
przed scoringiem.

C2 daje analogiczny, skończony certyfikat algebraiczny. C3 daje certyfikat
gauge/alignment, lecz potrzebuje jawnego rozdzielenia dwóch views.

# RELATION SYMMETRY BREAKING

W C1 relation effect ma zamkniętą postać: symetryzowana cross-covariance
poprawnych endpoints ma rank `d` i projector `A A^T`. Nie ujawnia kolumn `A`,
nazw latentów ani targetu. Wystarcza jednak do wyboru H1, ponieważ labeled
quadratic fit może wykorzystać `P_A x` razem z resztą płaskiego rekordu.

W C2 symmetry breakerem jest nullspace XOR differences. W C3 jest nim
cross-view alignment. Te trzy przypadki potwierdzają, że istotny jest
obserwowalny operator na relacji, nie nazwa przyszłej architektury.

# SHUFFLED/NULL RELATION CHECK

Dla C1 zamrożone semantyki ról są następujące:

- CORRECT: dokładnie `M_s`;
- SHUFFLED: fixed-point-free przestawienie prawych endpoints CORRECT,
  uwarunkowane na brak krawędzi z `M_s` lub `M_n`;
- RANDOM: niezależny uniform perfect matching o tym samym stopniu, również
  edge-disjoint od `M_s/M_n`;
- PASSIVE: te same relation slots i rekordy, lecz zero aktywnych krawędzi.

Wszystkie role muszą mieć bit-identical record tensor, label/mask tensor,
query tensor, target tensor, batch order, liczność, learner implementation,
stałe, capacity, steps i pełny budżet. Jedyną różnicą są endpoints/maska
relacji. SHUFFLED i RANDOM mają population relation cross-covariance 0;
kolizja z którymkolwiek ukrytym matchingiem jest błędem konstrukcji.

# TARGET LEAKAGE ANALYSIS

W C1 fixed-norm `s` i niezależny Gaussian probe `q` dają
`y|s ~ N(0,1)` dla każdego źródła. Dla poprawnej pary dwa probes są niezależne,
więc `(y_i,y_j)|edge` ma dokładnie rozkład `N(0,I_2)`, taki sam jak dla null
pair. Relation graph powstaje przed probes i nie czyta targetów. Auxiliary
records nie mają widocznych etykiet.

Relacja nadal niesie zamierzony sygnał: mówi tylko, że dwa anonimowe zdarzenia
pochodzą z tego samego trwałego źródła. Nie mówi, która współrzędna jest
stabilna, co jest nuisance, jaka jest wartość targetu ani jaki probe pojawi się
w query. Subspace istotną dla targetu trzeba wywnioskować z kowariancji par i
labeled train; nie jest zapisana w edge metadata.

C2 może uzyskać analogiczną exact-uniform parity kontrolę. C3 również może
usunąć korelację targetów przez niezależne probes, ale jawny view membership
pozostaje osobnym przeciekiem struktury, nie targetu.

# OOD DISCRIMINATOR

IID zachowuje `n=s`. OOD łamie wyłącznie tę równość: `s` i `n` są niezależne,
mają ten sam margines i nie zmienia się mechanizm targetu
`y=q^T s/sqrt(d)`. To bezpośrednio testuje wybraną niejednoznaczność, zamiast
zwiększać ogólny noise.

Dla C1 znormalizowane population risks są zamrożonym sanity targetem:

| predictor | IID NRMSE | OOD NRMSE |
|---|---:|---:|
| H1 stable | 0 | 0 |
| H2 swapped | 0 | `sqrt(2)` |
| symmetric passive extension | 0 | `1/sqrt(2)` |

K=`64/256/1024` zmienia wyłącznie liczbę niezależnych źródeł i relacji.
Wymagany jest ten sam learner i wszystkie role na każdej skali. Nie zamrożono
progu promotion ani finite-sample score; to wymaga późniejszego, osobnego
service audit i nie może być dobrane po wyniku.

# CLASSICAL CONTROL FEASIBILITY

Dla C1 obowiązkowy strong control jest w pełni legalny i prosty:

1. oblicza symetryczną cross-covariance poprawnych pairs;
2. bierze jej top-`d` spectral projector;
3. fituje regularized degree-2 regression na features z jednym czynnikiem
   projektowanym do tej subspace;
4. rozlicza acquisition, relation construction, eigendecomposition, fit,
   query, update, state, bytes touched i workload end-to-end.

Obowiązkowe controls obejmują też relation-free degree-2 ridge, CCA/kernel-CCA,
H1/H2 diagnostics oraz SHUFFLED/RANDOM/PASSIVE ablations. C2 ma exact
Gaussian-elimination/nullspace control, a C3 orthogonal Procrustes/CCA.
Istnienie tych controls jest zaletą kalibracyjną. Jeśli learned candidate nie
jest Pareto-nondominated względem nich, wynik jest negatywny niezależnie od
tego, czy relacja poprawia accuracy.

# ONTOLOGY FIREWALL

Dozwolony publiczny interfejs C1 zawiera wyłącznie płaskie rekordy, label mask,
targety labeled train, anonimową listę par/maskę oraz pojedyncze flat queries.
Nie zawiera `source_id`, `M_s`, `M_n`, nazw bloków, `A/B/D`, inverse mixing,
latentów, family/view IDs, nuisance labels, split helpers ani semantic channel
names. Kandydat nie może branchować po roli lub benchmarku.

Matching CORRECT ma candidate-neutral semantykę acquisition: „dwa pomiary
tego samego trwałego źródła”. Implementacja domenowa musi wykazać, że taka
relacja powstaje naturalnie i naliczyć jej koszt. Simulator-private matching
nie jest dowodem naturalnej dostępności.

C2 odpada na tym etapie: field operations i parity są gotową, wąską ontologią
problemu. C3 wymaga jawnej tożsamości dwóch views/modalności i dlatego nie
spełnia najmocniejszej wersji firewallu.

# CROSS-FAMILY PORTABILITY

C1 ma jeden abstrakcyjny interfejs możliwy do mapowania na repeated sensor
measurements, niezależne rejestracje tego samego procesu lub powtórne odczyty
tego samego obiektu. Nie jest to jeszcze cross-family evidence. W każdej
rodzinie trzeba niezależnie udowodnić, że relation acquisition nie korzysta z
ukrytego simulatora ani target semantics oraz że powtórzenie faktycznie zmienia
nuisance.

C2 jest przenośny głównie między problemami o znanej algebraicznej strukturze
GF(2). C3 przenosi się między multimodalnymi/alignment tasks, lecz view labels
i korespondencja są domenowym interfejsem. Tylko C1 pozostaje kandydatem do
późniejszej próby source-identical cross-family; nawet dla niego confidence w
naturalną dostępność relacji jest średnie, nie wysokie.

# PRIOR-ART/NEXTAI DUPLICATION

Passive non-identifiability bez dodatkowych założeń jest znanym ograniczeniem
([SRC-0164](https://proceedings.mlr.press/v97/locatello19a.html)); istnieją też
formalnie nierozróżnialne training tasks o różnych konsekwencjach transferu
([SRC-0246](https://proceedings.mlr.press/v9/david10a.html)). Paired views jako
symmetry breaker są również prior art: multi-view nonlinear ICA
([SRC-0235](https://proceedings.mlr.press/v115/gresele20a.html)), weakly
supervised pairs ([SRC-0237](https://proceedings.mlr.press/v119/locatello20a.html))
i augmentation pairs
([SRC-0244](https://proceedings.neurips.cc/paper/2021/hash/8929c70f8d710e412d38da624b21c3c8-Abstract.html)). CCA/kernel-CCA jest
obowiązkowym klasycznym control, nie nową ideą
([SRC-0245](https://jmlr.org/papers/v8/fukumizu07a.html)).

Dlatego C1 nie jest roszczeniem nowości dla contrastive learning ani CCA.
Nowy względem dotychczasowego NEXTAI jest węższy kontrakt falsyfikacyjny:
PASSIVE zawiera dwie symetryczne, równie realne repeated-measurement
struktury; labeled support czyni H1/H2 punktowo równymi; dopiero anonimowa
relation wybiera jedną, a OOD łamie dokładnie tę równość.

Najbliższe wcześniejsze testy nie są exact duplicate:

- `EXP-20260830-0038` behavioral conjugacy miał kompletny relational graph,
  który exact/MDL control wykorzystywał jako sufficient statistic;
- `EXP-20260901-0054/0056` pair-trained addressing miał raw/frozen exact
  neighbor controls i nie zawierał twin-world passive equivalence;
- `EXP-20260901-0003` testował równoważne kodowania operatora, lecz exact
  interpreter już rozwiązywał query bez relacyjnego symmetry breakera;
- cycle 240 miał repeated measurements, ale nie dwie exact-equivalent
  reprezentacje z przeciwnym OOD extension.

# CONTRACT RANKING

| rank | contract | exact H1/H2 ambiguity | ontology firewall | strong classical control | NEXTAI decision |
|---:|---|---|---|---|---|
| 1 | C1 orthogonal double-matching swap | PASS | PASS warunkowy na legalną acquisition | spectral covariance + projected quadratic ridge | jedyny ważny contract |
| 2 | C2 GF(2) double-matching swap | PASS | FAIL: field/parity ontology | exact nullspace/Gaussian elimination | odrzucony jako domain-specific calibration |
| 3 | C3 cross-view frame alignment | PASS | FAIL: jawny view partition | Procrustes/CCA | odrzucony jako prior/NEXTAI duplicate boundary |

C1 wygrywa nie dlatego, że jest trudniejszy, lecz dlatego, że ma exact
observational equivalence, candidate-neutral flat interface, analityczny OOD
gap i nie potrzebuje słabego baseline'u. C2 i C3 pozostają udokumentowanymi
negatywnymi alternatywami; nie wolno do nich wracać przez zmianę nazwy.

# DECISION

**A — ONE_VALID_IDENTIFIABILITY_CONTRACT.** Zamrożono wyłącznie pytanie
przyczynowe, observation boundary, semantykę ról, certyfikat H1/H2, bezpośredni
OOD discriminator, trzy skale źródeł i obowiązkowe controls C1 pod identyfikatorem
review-only `RID-CONTRACT-001`.

Nie zamrożono ani nie utworzono evaluatora, benchmarku, schematu, kandydata,
hipotezy, planu, seeda, progu sukcesu ani wyniku. Nie utworzono
`anonymous_repeated_measurement_ood_v2`. Confidence wynosi `0.93` dla
matematycznej nieidentyfikowalności C1, `0.84` dla braku target leakage przy
zadeklarowanym probe contract i `0.55` dla możliwości legalnego naturalnego
acquisition w kilku rodzinach. Żadna confidence hipotezy naukowej nie ulega
zmianie.

Experiment ID: brak. Immutable plan path: brak. Integrity/budget: review-only,
zero scoringu i zero runner-random seeda; pełne bramki końcowe są raportowane
w maszynowym checku cyklu.

Dokładny następny krok rozstrzygający to osobny chroniony cykl serwisowy bez
planu i scoringu: zbudować minimalny evaluator dokładnie dla
`RID-CONTRACT-001`, a następnie spróbować go sfalsyfikować przez twin-world
PASSIVE equality, role bit-identity, collision-free null relations, exact
target-leakage distribution i legalne classical controls. Jakikolwiek
passive-only discriminator H1/H2 lub brak exact H1/H2 OOD gap zatrzymuje
kontrakt przed eksperymentem. Dopiero późniejszy wake po pełnym PASS mógłby
prerejestrować jeden quick; ten cykl go nie autoryzuje.
