# OBSERVATION

Cykl 244 jest wyłącznie autoryzowanym cyklem serwisowym. Nie utworzono
hipotezy, immutable experiment planu, kandydata, runner-random seeda ani
wyniku i nie wykonano scoringu. Nie zmieniono żadnego ukończonego planu,
wyniku ani analizy.

Użytkownik udzielił trwałej zgody na lokalne instalowanie narzędzi i
zależności, pobieranie publicznych licencjonowanych danych oraz wykonywanie
testów potrzebnych NEXTAI bez kolejnych pytań. Jedyną nową bramką jest miejsce
na dysku: każda instalacja i akwizycja musi zostawić co najmniej 10 GiB wolnego
miejsca, a operacja o nieograniczonym bezpiecznie rozmiarze jest zatrzymywana.
Zakazy zewnętrznych modeli/API, sekretów, płatnych usług, publikacji,
deploymentu i destrukcyjnych zmian pozostają bez zmian. Zgodę zapisano w
`AGENTS.md`, a procedurę w `program.md`.

# DEPENDENCY ACQUISITION

Przed instalacją dysk C miał `96,597,528,576` wolnych bajtów. `uv add`
zainstalował i zamroził `pyamg==5.3.0` oraz jego zależność `scipy==1.18.1`.
Pobrane wheels miały około 1.6 MiB i 34.9 MiB. Import i wersje zostały
sprawdzone lokalnie. Po instalacji pozostało `96,549,728,256` wolnych bajtów.
Nie dodano modelu, API ani remote runtime.

# PROSPECTIVE DATA FREEZE

Przed pobraniem matrix payloads zamrożono
`research/data/suitesparse_real_pde_v1/acquisition_manifest.json`. Selection
używała wyłącznie snapshotu `ssstats.csv` SHA-256
`9bc797ab989331afbc9e0e51236d9145c2ac7f76c0913e9677ae07c4913a2aad`
z rewizji `31-Oct-2023 18:12:37`, bez oglądania jakości solvera.

Wybrano dziewięć realnych, square, index-positive-definite 2D/3D matrices:
po trzy rozmiary z computational fluid dynamics, structural engineering i
electromagnetics. Candidate-visible application labels, group i names są
zabronione w przyszłym learnerze. Wszystkie archives i extracted payloads są
lokalne i gitignored; tracking obejmuje manifest, licencję CC-BY 4.0,
collection/matrix citations i SHA-256.

Łączny archive footprint wyniósł `86,001,863` bajty, a 12 extracted files
`208,885,498` bajtów. Po pobraniu, ekstrakcji i audycie pozostało
`96,258,686,976` bajtów, więc 10 GiB gate przeszedł z bardzo dużym zapasem.

# ALGEBRAIC AUDIT

Wszystkie dziewięć macierzy ma zgodne dimensions, skończone wartości, dokładną
symetrię do `1e-12`, dodatnie diagonal entries i numerical nonzero count zgodny
z zamrożonym indeksem. `cfd2`, `msc01050` i `vanbody` zawierają odpowiednio
2492, 2958 i 7842 jawnie zapisane zera. Pierwszy audit błędnie porównał index
numerical-nnz ze SciPy stored-entry count; wynik zachowano, a końcowy audit
raportuje oba liczniki oddzielnie.

# CLASSICAL CONTROL PREFLIGHT

Na każdej macierzy zbudowano bez family-specific settings:

- standard PyAMG smoothed aggregation;
- adaptive smoothed aggregation z jednym kandydatem i pięcioma candidate
  iterations;
- CG preconditioned każdą hierarchią;
- ponowne użycie tej samej adaptive hierarchy dla drugiego deterministycznego
  RHS.

Pierwszy jawny contract `rtol=1e-8`, `maxiter=500` nie przeszedł adaptive SA
dla `cfd2`, `bcsstk36` i `vanbody`; standard SA nie domknął `bcsstk36` ani
`vanbody`. Failed audit jest zachowany jako
`audit_attempt_001.json`, SHA-256
`7c23b36795d79e06c67f54caeb94bc3f81928417f940179fed38164502b90718`.

Końcowy wspólny feasibility contract `rtol=1e-7`, `atol=0`, `maxiter=2000`
przeszedł dla obu kontrolek i obu RHS na wszystkich dziewięciu macierzach.
Adaptive SA potrzebował jednak aż 1598 iteracji na primary i 1589 na reused
RHS dla `bcsstk36`, podczas gdy standard SA potrzebował 440. To ważna
obserwacja: adaptive discovery jest uruchamialne, lecz nie jest automatycznie
najsilniejszym ani najtańszym control. Przyszły plan musi zachować oba i nie
może nazywać adaptive SA oracle.

Final audit SHA-256 to
`8f4e2c023f12fbf2a04e8f0fa111a5386e67c7bded0d997c634a2e5f44776ed2`.
Wall time jest tylko diagnostic; candidate comparison musi używać także
operations, sparse matvecs, bytes, setup, state i declared solve horizons.

# INTERPRETATION

Realny corpus i klasyczne AMG controls są technicznie wykonalne. Aparatura
potrafi teraz rozstrzygnąć, czy learned local prolongation rule przewyższa
per-instance standard i adaptive AMG przy matched residual oraz czy meta-fit
amortyzuje się przez wiele RHS tej samej macierzy.

Nie potrafi jeszcze uczciwie rozstrzygnąć pełnej wersji tezy z cyklu 243 o
recycling między **zmieniającymi się** macierzami. Dziewięć niezależnych
SuiteSparse matrices nie tworzy kontrolowanej parameterized sequence o tym
samym rozmiarze i sparsity topology. Ponowne użycie hierarchy na drugim RHS
bada same-matrix amortization, nie preconditioner update między A(p_k).
Usunięcie tej kontrolki osłabiłoby causal thesis i jest niedozwolone.

# UNCERTAINTY

SuiteSparse `posdef=1`, dodatnia przekątna, symetria i zbieżność CG z AMG są
mocnym feasibility evidence, ale nie formalnym exact Cholesky certificate dla
największych macierzy. RHS w audycie są syntetyczne i służą wyłącznie smoke
testowi; nie są benchmark targets. Koszty Python/PyAMG nie reprezentują
automatycznie zoptymalizowanego compiled solvera, dlatego finalne wnioski muszą
opierać się na pełnym operation/byte boundary oraz jasno oznaczonym wall time.

# CONFIDENCE

Confidence `0.99`, że dependency, payload hashes, disk gate i algebraic smoke
są poprawne. Confidence `0.97`, że standard/adaptive SA oraz same-matrix reuse
są uruchamialne na całym zamrożonym subset. Confidence `0.95`, że obecny corpus
nie wystarcza do uczciwego testu cross-matrix recycling bez dodatkowej
prospektywnej relacji między systemami.

# DECISION

`PARTIAL_PASS_REAL_PDE_CORPUS_NEEDS_RECYCLING_DISCRIMINATOR`.

Experiment ID: brak (service-only). Immutable plan path: brak. Nie zmieniono
formalnego evidence ani confidence hipotez. Nie wolno jeszcze prerejestrować
scored experiment.

# NEXT DISCRIMINATING EXPERIMENT

Dokładny następny krok to jeden no-scoring search/service cycle: znaleźć w tym
samym licencjonowanym SuiteSparse snapshot co najmniej jedną prospektywną parę
lub sekwencję realnych SPD matrices o zgodnym dimension i sparsity topology,
która pozwala uruchomić classical hierarchy/preconditioner recycling bez
family labels. Jeżeli snapshot nie zawiera takiej sekwencji, należy zawęzić lub
odrzucić REAL-PDE-THESIS-001 zamiast budować benchmark, który pomija najmocniejszą
kontrolkę. W następnym cyklu nadal nie wolno tworzyć HYP, planu, kandydata,
seeda ani scoringu.
