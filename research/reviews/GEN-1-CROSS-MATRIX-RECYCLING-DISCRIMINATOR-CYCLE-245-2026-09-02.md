# OBSERVATION

Cykl 245 jest jednym ograniczonym no-scoring search/service cycle. Nie
utworzono formalnej hipotezy, immutable experiment planu, kandydata,
evaluatora, runner-random seeda ani wyniku i nie wykonano scoringu. Nie
zmieniono historycznego RID evaluator ani jego decyzji K.

Z zamrożonego `ssstats.csv` wybrano przed pobraniem wszystkie dostępne rodzaje
realnych, square, index-positive-definite 2D/3D pair candidates o tym samym
SuiteSparse group, dimension, numerical nnz i application kind. Snapshot miał
cztery metadata groups: dwie thermal, jedną CFD i jedną generic 2D/3D. Aby nie
duplikować rodzaju, prospektywnie wybrano mniejszą thermal pair oraz po jednej
CFD i generic pair; druga thermal pair została wykluczona przed outcome.

Zamrożone sekwencje:

| Slot | Source -> target | N | Relative numeric change |
|---|---|---:|---:|
| thermal | `ted_B -> ted_B_unscaled` | 10,605 | 0.00210994 |
| CFD | `shallow_water1 -> shallow_water2` | 81,920 | 1.54500166 |
| generic 2D/3D | `fv2 -> fv3` | 9,801 | 0.13853445 |

Każda para ma pointwise-identical CSR sparsity pattern. Archiwa miały łącznie
`6,540,007` bajtów, extracted payload `18,846,640` bajtów. Wolne miejsce
zmieniło się z `96,247,271,424` do `96,242,802,688` bajtów; 10 GiB disk gate
przeszedł.

# FROZEN CLASSICAL CONTROLS

Każdy target użył tego samego deterministic RHS, `rtol=1e-7`, `atol=0` i
`maxiter=2000`. Bez family-specific settings uruchomiono standard SA i
adaptive SA w trzech trybach:

1. pełny target rebuild;
2. frozen hierarchy z source matrix, z wymianą fine solve matrix;
3. zachowane source P/R z ponownym przeliczeniem wszystkich Galerkin coarse
   operators i smootherów na target values.

Target rebuild był kompletny dla obu solverów na wszystkich parach. Standard
SA potrzebował odpowiednio 1, 5 i 6 CG iterations, adaptive SA 1, 6 i 6.

# RECYCLING OUTCOMES

**Thermal:** wszystkie reuse variants zbiegły w jednej iteracji. Zmiana jest
niemal czystym rescalingiem i klasyczne reuse dostarcza cały efekt; taki wynik
nie może być credit dla learnera.

**CFD:** standard frozen/refresh potrzebował 10 iteracji względem 5 po rebuild;
adaptive frozen potrzebował 13, a refresh 12 względem 6 po rebuild. Recycling
pozostaje poprawny, lecz około dwukrotnie pogarsza solve work; oszczędność setup
musi być rozliczona przez workload horizon.

**Generic 2D/3D:** target rebuild obu kontrolek zbiega w 6 iteracjach. Frozen
standard/adaptive kończy 2000 iterations z residual `0.05123/0.05903`.
Numeric coarse refresh również nie zbiega: residual `0.002991/0.012417`.
Jest to bounded, complete negative control outcome, nie timeout, crash,
missing metric ani semantic invalidation.

Audit SHA-256:
`82bac4874eac4cf94e89be5eeeae68b2011e20b658072482fdefd926bd824ea3`.

# CAUSAL DISCRIMINATOR

Sekwencje rozdzielają trzy wyjaśnienia:

- jeśli learned mapping pomaga tylko thermal, powiela trivial classical
  scaling/reuse;
- jeśli pomaga CFD, musi po pełnym koszcie pokonać zarówno 5/6-iteration
  target rebuild, jak i tańszy setup reuse z około 2x solve penalty;
- jeśli pomaga `fv2->fv3`, musi osiągnąć matched residual, podczas gdy source
  hierarchy nie przenosi się, oraz nadal pokonać 6-iteration target rebuild po
  doliczeniu acquisition i meta-fit.

Dlatego fail recycling control nie unieważnia przyszłego benchmarku. Kontrolka
wykonała się w pełnym budżecie i ujawniła realną granicę przenośności. Mocnym
alternatywnym solverem na tym target pozostaje poprawnie działający per-target
standard/adaptive rebuild.

# PROSPECTIVE LEARNER CONTRACT BOUNDARY

Późniejsza protected migration może utworzyć wyłącznie minimalny cohort
`heldout_suitesparse_cross_matrix_prolongation_v1` o następującej granicy:

- meta-training sources: dziewięć zamrożonych real matrices z cyklu 244 oraz
  trzy source matrices powyższych sekwencji;
- held-out targets: wyłącznie `ted_B_unscaled`, `shallow_water2` i `fv3`;
- candidate widzi tylko anonymous CSR numeric operator; group, name, kind,
  pair identity, geometry, PDE label i ręczny near-nullspace są zabronione;
- jeden source-identical local rule i stałe dla shared, independent,
  cross-family-only i support-only; role różnią się wyłącznie dozwolonym
  zakresem source matrices;
- mandatory controls: per-target standard SA, per-target adaptive SA, frozen
  source hierarchy, fixed-P/R numeric refresh i unpreconditioned CG;
- quality gate: finite solution i relative residual `<=1e-7`; max 2000 CG
  iterations jest completed low-quality outcome, nie infrastructure failure;
- full cost obejmuje matrix acquisition, meta-fit, hierarchy construction lub
  update, every SpMV/preconditioner application, bytes, resident/peak state,
  memory traffic oraz R1/R4/R16 solve horizons;
- sukces wymaga dodatniego shared-vs-independent i cross-family-only-vs-
  support-only efektu na każdym target, no worst-target regression oraz
  implementable Pareto non-dominance względem najlepszego rebuild/reuse
  wariantu przy matched residual.

Nie wolno creditować learnerowi samego wyboru między rebuild i reuse; taka
admission policy jest osobną prostą klasyczną kontrolką i jej decyzja/koszt
muszą być doliczone.

# INTERPRETATION

Cykl 244 słusznie stwierdził, że cross-matrix recycling nie było jeszcze
sprawdzone. Cykl 245 zamyka tę niewiadomą. SuiteSparse snapshot zawiera trzy
prospektywne same-pattern transitions o jakościowo różnych reuse outcomes, a
per-target rebuild jest mocny i kompletny w każdym przypadku. Aparatura może
więc rozstrzygnąć ostrzejszą tezę z cyklu 243 bez osłabiania classical control.

Nie jest to evidence za learned prolongation. Pokazuje tylko, że istnieje
realny, niejednorodny i falsyfikowalny test, w którym prosty reuse czasem
dostarcza cały efekt, czasem trade-off, a czasem zawodzi.

# UNCERTAINTY

Każdy slot ma tylko jedną source-target pair, więc przyszły quick będzie
screeningiem, nie dowodem ogólnej klasy PDE. `generic 2D/3D` nie jest
semantycznie wąską application family; label pozostaje evaluator-private, ale
minimum-family claim musi być ostrożny. PyAMG reprezentuje mocne, utrzymywane
kontrolki, lecz nie każdy możliwy published preconditioner update. Wall time
jest diagnostic i nie może zastąpić operation/byte accounting.

# CONFIDENCE

Confidence `0.995`, że pattern identity, hashes, solver executions i residuals
są poprawnie zapisane. Confidence `0.97`, że trzy sekwencje tworzą użyteczny
screening discriminator przeciw frozen hierarchy i numeric coarse refresh.
Confidence `0.62`, że jeden mały source-identical learner ma szansę pokonać
6-iteration per-target rebuild po pełnym koszcie; ta niska prior probability
jest właśnie powodem, by ewentualny quick był tani i rozstrzygający.

# DECISION

`KEEP_DISCRIMINATOR_AUTHORIZE_PROTECTED_EVALUATOR_MIGRATION_ONLY`.

Experiment ID: brak (service-only). Immutable plan path: brak. Nie zmieniono
formalnego hypothesis evidence ani G1 count. Scoring pozostaje zabroniony.

# NEXT DISCRIMINATING EXPERIMENT

Dokładny następny wake to jedna protected, service-only migration do
`heldout_suitesparse_cross_matrix_prolongation_v1`: zamrozić wyłącznie powyższe
source/target split, anonymous CSR boundary, pięć controls, cztery
source-identical roles, residual/cost contract, leakage fixtures i pre-seed
control audit. Nie tworzyć HYP, planu, kandydata, seeda ani scoringu. Jeżeli
semantic/source-identity, target isolation, matched-residual controls,
integrity lub doctor nie przejdą, pozostawić maintenance i nie otwierać v2.
