# OBSERVATION

Cykl 240 był wyłącznie chronioną migracją evaluatora i audytem kontraktu
`BRIDGE-U1-U2-V1`. Nie utworzono `HYP-*`, planu, kandydata ani wyniku; nie
zrealizowano runner-random scoring seed i nie wykonano candidate scoringu.
Deterministyczny seed `240031` służył wyłącznie publicznym/dev fixtures.
`EXP-99` nie powstał.

Wszystkie bramki konstrukcyjne evaluatora przeszły, lecz test rozstrzygający
PASSIVE wykazał `P3`: prosta kontrolka bez relacji rozwiązuje użyteczną część
zadania na największej zamrożonej skali. Jest to wada zdolności kontraktu do
rozróżniania tezy, a nie negatywny wynik learned mechanizmu.

# EVALUATOR MIGRATION

Utworzono dokładnie zamrożony evaluator
`src/nextai_autoresearch/benchmarks/anonymous_repeated_measurement_ood_v1.py`
oraz mały publiczny boundary
`src/nextai_autoresearch/relational_ood_contract.py`. Generator ma wymiar
ukryty 16, wejście 32, K=`64/256/1024`, dwa pomiary na źródło, 256 query na
warunek, cztery pojedyncze nuisance train, S1/S2/S3 jako niewidziane kombinacje,
target `y=z^Tq/16`, bit-reversal jako main i `pi(j)=(7j+3) mod 32` jako wariant
adversarial. Relacja jest fit-only, a query jest pojedynczym rekordem.

Kohorta jest zamrożona jako osobne
`anonymous_repeated_measurement_ood_v1` ze statusem `maintenance` i
`scoring_authorized=false`. Poprzedni manifest
`heldout_repository_sequence_compression_v6` zachowano append-only pod
`research/manifests/heldout_repository_sequence_compression_v6-protocol-v2-52f480d057f7.json`.
Żaden ukończony plan, wynik ani analiza nie został zmieniony.

# CONTRACT HASHES

- evaluator file SHA-256:
  `d70674b667e6f2ddf9b92a4fcddb1d42e41fde5a423ab8969260253a3de2afec`;
- public contract SHA-256:
  `26f561268fa9dbdccc90fdfc904d70e45f9fa98671045db0a3de6d1eddf9f81b`;
- protected evaluator bundle:
  `f60b975b5128d76eee6a018fe641d2a21de2f5267e0d607290a1400b0f7d9af7`;
- manifest SHA-256:
  `62380acd396ecb7ea68c5b5db6c64be18353d9059b7cf1d03e9908de2da62739`;
- preflight payload certificate:
  `6effd9103017e23c788fb10bb0b547b8540b9d3a34e962d7e859b4e785cf9992`.

Maszynowy zapis audytu znajduje się w
`research/checks/anonymous_repeated_measurement_ood_v1_cycle_240.json`.

# ROLE BIT-IDENTITY

Role `correct/shuffled/passive/random/classical/oracle` mają identyczne:

- records: `4c775d0a...093c6d`;
- targets: `002531bd...7a1f8f`;
- query records: `56b0234e...d3e4`;
- query targets: `02f87d5a...95f2`;
- batch order: `5ccf19f4...f25d`.

Pełne 64-znakowe hashe są zapisane w check JSON. Relation-table hash różni się
wyłącznie dla `shuffled` i `random`; PASSIVE ma ten sam payload relacji co
CORRECT, ale wszystkie maski są fałszywe. Test bit-identity: PASS.

# RELATION CONSTRUCTION AUDIT

CORRECT relation powstaje z acquisition membership natychmiast po latent
records i przed `q`, targetem oraz nuisance. Shuffled i random tables również
istnieją w acquisition order przed jednym wspólnym globalnym batch shuffle.
Konstruktor nie czyta targetu ani nuisance.

Na K=1024: CORRECT ma 1024 prawdziwe edges i stopień 1; SHUFFLED ma 1024 edges,
stopień 1, zero prawdziwych par i zero fixed points; RANDOM jest perfect
matchingiem ze stopniem 1 i zerem prawdziwych par; PASSIVE ma ten sam interfejs,
1024 slots i zero aktywnych edges. PASS.

# TARGET LEAKAGE AUDIT

Empiryczne MI `edge_truth; (y_left,y_right)` wynosi `0.02545` bit, korelacja
edge truth z `|y_left-y_right|` wynosi `0.03701`, a korelacja target-target dla
poprawnych par `0.00346`. Dokładny TV między rozkładami targetu warunkowanymi
źródłem wynosi 0, ponieważ niezależny Rademacher `q` daje ten sam rozkład `y`
dla każdego `z`. Index/order-only ridge ma względny gain `0.00155` nad nullem.
Żaden test nie przekroczył zamrożonej bramki leakage. PASS.

# SOURCE IDENTITY LEAKAGE AUDIT

Przy losowym shuffle chance odzyskania partnera wynosi `0.0004885`. Recall dla
ataków adjacent, mirror, cyclic i nearest-in-target-order wynosi odpowiednio
`0`, `0`, `0.0004883`, `0`. Publiczny payload nie zawiera source/event ID,
nuisance, nazw plików ani stabilnego acquisition order. PASS.

# PASSIVE INFORMATION SUFFICIENCY

Wynik to `P3 - simple classical sufficient statistic solves the useful task`.
Degree-2 polynomial ridge używa tylko anonimowych płaskich rekordów i targetów,
bez relacji, prywatnego splitu lub simulator state. NRMSE:

- K=64: IID/S1/S2/S3 = `0.894/0.924/0.877/0.985`;
- K=256: `1.080/1.235/1.050/1.387`;
- K=1024: `0.307/0.522/0.538/0.653`.

Na K=1024 wszystkie trzy OOD cells przechodzą zamrożony useful-quality ceiling
`NRMSE <= 0.75`. Target jest funkcją stopnia drugiego candidate-visible input,
a single-record query nie otrzymuje relacji. Relacja może zatem zmienić
finite-sample estimation, lecz nie wybiera reprezentacji zawierającej nową
informację query-side. Obowiązkowa all-scale classical-control conjunction nie
może rozstrzygnąć zamierzonej tezy.

Niepewność: wartości pochodzą z jednego deterministycznego development fixture,
więc nie estymują wariancji naukowego wyniku. Decyzja E nie opiera się na
promocji score; opiera się na konstrukcyjnym bilinear boundary i wykazanej
implementowalności prostej kontrolki poniżej zamrożonego sufitu.

# PERMUTATION AUDIT

Five-bit reversal i `pi(j)=(7j+3) mod 32` są bijekcjami. Obie zachowują target i
evaluator-only oracle dokładnie; wspólny oracle target hash to
`ccbe529d...c4883`. Candidate-visible API nie zawiera inverse permutation,
split helpera, roli ani semantic channel names. PASS.

# ORACLE SANITY

Oracle oblicza wyłącznie evaluator-side `z^Tq/16`. Maksymalny absolute error
wynosi dokładnie 0 dla IID/S1/S2/S3, K=`64/256/1024` oraz obu permutacji. Oracle
nie jest kandydatem ani evidence. PASS.

# CLASSICAL CONTROL FEASIBILITY

Uruchomiono legalne ścieżki dla: degree-2 polynomial ridge, symmetric linear
CCA + degree-2 ridge oraz explicit degree-2 kernel CCA/ridge. Wszystkie używają
wyłącznie public records, train targets i - gdy dana kontrolka tego wymaga -
public relation edges. Stałe zamrożone data-free przed jakimkolwiek score to:
ridge/CCA regularization `1e-3`, rank `16`, tolerance `1e-10`. Projekcje
`32x16` i `560x16` są finite. PASS.

# NUISANCE SANITY

Analityczny RMS corruption dla S1/S2/S3 rośnie
`0.4719 < 0.5590 < 0.7181`; development fixture daje
`0.4730 < 0.5586 < 0.7174`. Query zachowuje ten sam target mechanism i zmienia
wyłącznie wcześniej zadeklarowane nuisance. PASS.

# SCALE SANITY

K=`64/256/1024` daje dokładnie `128/512/2048` rekordów treningowych i
`64/256/1024` poprawnych relacji. Każda skala ma cztery warunki query po 256,
czyli 1024 query. Nie ma subsamplingu ani zmiany formuły między skalami. PASS.

# PROTECTED BOUNDARY

Public query nie zawiera targetów. Existing benchmark-boundary audit potwierdza
brak importu kodu kandydata przez evaluator. Dodany mały AST gate odrzuca
fixture próbujące użyć private state, evaluator role branching albo
candidate-owned RNG. `run_suite` evaluatora ma jawny hard stop, a konfiguracja
`maintenance` zatrzymuje plan/scoring gate. Nie powstał learned role ani
benchmark-specific candidate. PASS.

# COST ACCOUNTING

Publiczny schema wymaga: acquisition ops/bytes, relation construction,
synchronization, preprocessing, fit, query, update, bytes touched, state,
peak, workload R1/R4/R16 oraz wall time jako diagnostyki. Pusty lub częściowy
cost record nie może ominąć żadnego pola; wszystkie wartości muszą być
nieujemne. W tym service audit nie raportuje się tych pól jako wyniku
kandydata. PASS.

# TESTS

Dedykowane semantic/contract/preflight tests: 40 PASS. Pełny `pytest`: 639
PASS. Testy obejmują exact constants, kolejność konstruktora, bit identity,
edge semantics, leakage attackers, source identity, oba permutation variants,
oracle na wszystkich skalach, classical feasibility, P3, nuisance, scale,
deterministic rerun, protected boundary, cost schema i hard stop scoringu.

# INTEGRITY

Preflight obejmujący evaluator, runner, schemas, baseline registry i manifest:
PASS. `nextai integrity verify`: PASS, 799 plików, evaluator bundle
`f60b975b...d9af7`. `nextai doctor`: PASS; benchmark widoczny jako
`anonymous_repeated_measurement_ood_v1 status=maintenance`, pending plans 0.
Poprzedni manifest jest zachowany append-only. Nie dodano zależności, API,
zewnętrznego modelu ani danych.

# DECISION

`E - benchmark cannot discriminate relational advantage`.

Confidence: wysokie dla tej wady kontraktu, bez zmiany confidence żadnej
hipotezy naukowej. Evaluator i negatywna historia pozostają zachowane, ale
scoring jest niedozwolony. Nie wolno w tym cyklu naprawiać targetu, progów,
kontrolek, korupcji lub skal, tworzyć v2, kandydata, planu ani `EXP-99`.

Experiment ID: brak (service-only). Immutable plan path: brak. Dokładny następny
eksperyment rozstrzygający: żaden nie jest autoryzowany pod tym kontraktem.
Najbliższy dozwolony wake powinien być osobnym strategicznym wyborem
jakościowo innego pytania, w którym relacja zmienia dostępną informację albo
identyfikowalność, a nie tylko finite-sample estymację tej samej jawnej funkcji;
nie może automatycznie tworzyć v2 ani score.
