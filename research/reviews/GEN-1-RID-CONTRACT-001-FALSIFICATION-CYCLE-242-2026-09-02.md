# OBSERVATION

Cykl 242 był wyłącznie chronioną migracją i próbą sfalsyfikowania
`RID-CONTRACT-001`. Nie utworzono `HYP-*`, immutable experiment planu,
learned candidate, architektury ani `EXP-99`; nie zrealizowano runner-random
scoring seed i nie wykonano candidate scoringu. Deterministyczny seed
`242001` służył tylko fixture'om audytowym.

Czternaście z piętnastu mechanicznych grup kontroli przeszło. Obowiązkowa
zamrożona grupa classical spectral/CCA nie przeszła własnej koniunkcji jakości:
CCA działa niemal dokładnie, lecz zamrożona ścieżka spectral ma przy K=1024
OOD NRMSE `1.539751`, powyżej progu `0.40`. Decyzja to
`K_CONTRACT_FAIL_OTHER`. Nie zmieniono po wyniku kodu, progów ani kontraktu.

# RID-CONTRACT-001 IMPLEMENTATION

Powstał odrębny evaluator
`orthogonal_double_matching_source_swap_v1`, bez modyfikowania historycznego
`anonymous_repeated_measurement_ood_v1`. Używa d=16, input=48,
K=`64/256/1024`, ortogonalnego `[A B D]`, rekordu `x=A*s+B*n+D*q`, sferycznych
`s,n`, Gaussowskiego `q`, train/IID `n=s`, OOD z niezależnymi `s,n` i targetu
`q^T*s/sqrt(d)`. Publiczny boundary zawiera wyłącznie anonimowe rekordy,
legalne targety treningowe, maskę etykiet i anonimową tabelę/maskę relacji.
Evaluator jest zachowany jako `maintenance`; scoring ma twardy stop.

Labeled train count `2048`, IID query count `4096` i OOD query count `4096`
są stałymi fixture'ów implementacyjnych. Jedyną wielkością skalowaną przez K
jest liczba niezależnych źródeł pomocniczych/próbek relacji.

# TWIN-WORLD CERTIFICATE

PASS. Transformacja `A<->B`, `s<->n`, `M_s<->M_n` daje byte-identical legalny
PASSIVE transcript. Hashe publicznych records, targets, label mask, relation
slots/mask, batch order, IID/OOD queries i metadata są identyczne w W i
W_swap. Maksymalny błąd ponownego złożenia wynosi `8.882e-16`; targety train i
IID są byte-identical. OOD public records pozostają identyczne, a ukryta
interpretacja poprawnego mechanizmu zamienia stronę.

# H1/H2 TRAIN-IID EQUALITY

PASS. `s=n` zachodzi pointwise dla każdego labeled train record. Maksymalne
błędy H1-H2 na train, H1-target na train i H1-H2 na IID wynoszą dokładnie `0`.

# OOD DISCRIMINATOR

PASS na deterministycznym fixture 65,536. NRMSE H1=`0`, H2=`1.420260` wobec
`sqrt(2)=1.414214`, symmetric=`0.710130` wobec `1/sqrt(2)=0.707107`.
Znormalizowany cross moment s/n wynosi `0.01633`; maksymalny błąd promienia
sfery `1.33e-15`. Analityczne MSE to odpowiednio `0/2/0.5`.

# CORRECT RELATION OPERATOR

PASS. Dla sześciu prerejestrowanych fixture'ów na skalę średni overlap
span(A) rośnie `0.7148 -> 0.9300 -> 0.9837`, a względny błąd operatora maleje
`1.1101 -> 0.5571 -> 0.2818`. Przy K=1024 overlap B=`0.00839`, D=`0.00787`,
CCA overlap A jest praktycznie `1`, minimalna signal eigenvalue `0.8222`, a
maximum noise eigenvalue `0.2185`. Empiryczny operator zbiega do `A*A^T`.

# NULL RELATION AUDIT

PASS. M_s i M_n są edge-disjoint perfect matchings. SHUFFLED i RANDOM mają
po K edges, stopień 1, zero self-edges i zero kolizji z obiema ukrytymi
relacjami. Ich operator norms maleją w trzech skalach; przy K=1024 wynoszą
`0.27054` (shuffled) i `0.26641` (random). Żaden overlap A/B/mix nie przekracza
zamrożonego limitu `0.55`.

# ROLE BIT-IDENTITY

PASS. CORRECT/SHUFFLED/RANDOM/PASSIVE są identyczne dla records, train targets,
label mask, query records/targets, batch order, counts, public constants,
code-path requirements i future capacity/steps/budget placeholders. Różnią się
wyłącznie endpointami i active mask. Pełne SHA-256 każdego wspólnego payloadu
i każdej relacji zapisano w maszynowym checku cyklu 242.

# TARGET LEAKAGE

PASS. Relacja powstaje przed q i targetem, a auxiliary targets nie są publiczne.
Target-target correlation=`0.02075`, target-gap/edge correlation=`0.01523`,
MI proxy=`0.00245` bit, paired endpoint predictor gain=`-0.00158`, a
index/degree/position gain=`-0.00341`. Wszystkie wartości pozostają poniżej
zamrożonych progów.

# ONTOLOGY FIREWALL

PASS. Query API ma tylko `records`; training API ma anonimowe records, legalne
targets, label mask, relation endpoints/mask i batch order. AST gate odrzuca
import protected evaluatora, role branching oraz identyfikatory stable latent i
world identity. Benchmark-boundary audit nie wykrył importu candidate code.

# PASSIVE IDENTIFIABILITY AUDIT

PASS. Degree-2 ridge osiąga train NRMSE `2.72e-10` i IID `3.85e-10`, lecz na
OOD ma H1/H2 NRMSE `0.70230/0.71318`. Finite-sample preference wynosi
`+0.0108796` w W i dokładnie `-0.0108796` w W_swap przy tej samej publicznej
predykcji. Jest to szum/inductive bias, nie systematyczna identyfikowalność.
Linear OOD NRMSE=`1.00719`; PCA+quadratic OOD NRMSE=`0.70171`.

# CLASSICAL SPECTRAL/CCA CONTROL

FAIL — jedyna nieprzechodząca grupa. Kontrolki używają wyłącznie publicznych
records, targetów train i exposed CORRECT edges; source audit potwierdza legalny
boundary. Zamrożono rank 16, ridge/CCA `1e-6`, eigensolver tolerance `1e-10`
i sign-invariant subspace projector.

Przy K=1024 spectral projector ma overlap A=`0.98425` i IID NRMSE=`0.09973`,
ale OOD NRMSE=`1.53975`, więc łamie frozen maximum `0.40`. CCA overlap A jest
`0.999999999999982`, IID NRMSE=`1.06e-7`, OOD NRMSE=`1.81e-6` i przechodzi
swój limit `0.45`. Ponieważ prerejestrowany gate wymagał całej grupy, obecność
jednej doskonałej kontrolki nie upoważnia do post-result reinterpretacji.

Niepewność: fail dotyczy konkretnej zamrożonej implementacji spectral
downstream i jej koniunkcji, nie analitycznej identyfikowalności RID jako takiej.
Naprawa byłaby nowym kontraktem w osobnym, jawnie autoryzowanym cyklu; w tym
cyklu jest zabroniona.

# SCALE SANITY

PASS. K=`64/256/1024` odpowiada dokładnie `128/512/2048` auxiliary records i
`64/256/1024` relation samples. D=16, input=48, 2048 labeled train records oraz
po 4096 IID/OOD queries pozostają stałe. Correct recovery i null decay mają
oczekiwany kierunek na wszystkich trzech skalach.

# FINITE-SAMPLE SYMMETRY

PASS. RNG streams, order konstrukcji, QR sign convention, batching, precision i
serialization zostały objęte explicit swap i deterministic rerun. Publiczny
transcript jest identyczny, a jedyna finite-sample preferencja pasywnego
estymatora zmienia znak pod paired world swap. Development fixture nie jest
traktowany jako scoring seed ani evidence kandydata.

# COST ACCOUNTING

PASS dla kompletności schematu. Pola obejmują acquisition ops/bytes, relation
construction/synchronization, preprocessing, spectral, fit, query, update,
bytes touched, state, peak, wall-time diagnostic i workload R1/R4/R16. Dla
K=1024 kontrolka raportuje m.in. fit ops `1.362693e9`, query ops `6.299648e6`,
state `12,296` B, peak `14,172,160` B i R16 `1.471769e9`. Wall time `0` oznacza
niezmierzony service diagnostic, nie darmowy koszt.

# TESTS

Dedykowany kontrakt: 19 PASS, 2 FAIL. Pełny pytest: 658 PASS, 2 FAIL z 660.
Obie porażki są oczekiwanym skutkiem tego samego hard gate: classical control
`pass=false` oraz final decision K zamiast A. Nie ma innych regresji.

Preflight certificate nie został przepisany po porażce. Verify prawidłowo
odrzucił stary certyfikat jako niezgodny z nowym manifestem. Utworzenie nowego
certyfikatu oznaczałoby fałszywe poświadczenie nieprzechodzącego evaluatora.

# INTEGRITY

Poprzedni manifest zachowano append-only jako
`research/manifests/anonymous_repeated_measurement_ood_v1-protocol-v2-28d94a66be61.json`.
Nowy maintenance manifest obejmuje 802 protected files i przechodzi integrity;
evaluator bundle SHA-256 to
`1b3f47c0a37db8baa361723e66470a4abb12e19ff285d9cd0c90be0e53b8093b`.
Evaluator file SHA-256:
`87ba587b8e972ac1a89e2d84469c28e8c7b72901f9389a2b98b5dbb54dc35c7d`;
public contract:
`f69e72e42fe4d2ebf86d09d1612b48d62011be16e6f30e0624c06569979333f7`.

Doctor widzi integrity PASS, pending plans 0 i brak scoring state, lecz kończy
FAIL dokładnie przez `RID-CONTRACT-001 falsification gate:
K_CONTRACT_FAIL_OTHER`. Jest to zamierzona blokada, nie błąd ukryty.

# DECISION

`K. CONTRACT_FAIL_OTHER` — odrzuć tę zamrożoną instancję evaluatora; nie
certyfikuj, nie naprawiaj w cyklu 242, nie twórz v2, learnera, HYP, planu,
runner seed, score ani EXP-99. Confidence jest wysokie dla statusu K, ponieważ
wynik jest deterministyczny i został powtórzony w dedicated oraz full suite;
nie zmienia on confidence żadnej hipotezy naukowej.

Experiment ID: brak (service-only). Immutable plan path: brak. Następny
eksperyment rozstrzygający: żaden nie jest obecnie autoryzowany. Dokładny
następny dozwolony krok to osobny no-scoring strategic review, który albo
zamyka RID branch, albo prospectively definiuje odrębny kontrakt i pełną
kontrolkę przed jakąkolwiek implementacją; nie wolno edytować ani ponownie
interpretować v1.
