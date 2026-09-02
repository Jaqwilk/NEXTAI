# OBSERVATION

Cykl 243 jest wyłącznie `SEARCH MODE`. Nie utworzono hipotezy, planu,
kandydata, evaluatora, benchmarku, schematu ani seeda i nie wykonano scoringu.
Nie zmieniono zamrożonego `orthogonal_double_matching_source_swap_v1`, jego
manifestu ani statusu `maintenance`. Aktywny hard gate pozostaje dokładnie
wynikiem K z cyklu 242.

Pełna synteza cyklu 237 wykazała siedem powtarzalnych przyczyn porażek. Dla
obecnego wyboru najważniejsze są: klasyczna metoda realizująca tę samą funkcję
taniej (RC2), brak amortyzacji pełnego kosztu (RC4), lokalność dopiero po
uzyskaniu poprawnego stanu/adresu (RC5) i brak przenośnego inwariantu między
rodzinami (RC7). Ostatnie ważne wyniki są zgodne z tą granicą: EXP-0059 miał
częściowy sygnał pooled representation bez foreign-family transfer, EXP-0060
nie przewyższył posterior mean/persistence/control bank, a EXP-0062 przegrał
z recurrence-disabled i PPM/CTW.

# RID BRANCH CLOSURE

`RID-CONTRACT-001` nie powinien generować kolejnego evaluatora ani kandydata.
Zamrożona kontrolka spectral nie przeszła kontraktu, ale legalna CCA osiągnęła
OOD NRMSE około `1.81e-6`. To oznacza, że relacja rzeczywiście niesie potrzebny
sygnał, lecz znana klasyczna statystyka odzyskuje go praktycznie dokładnie.
Naprawienie spectral path nie odsłoniłoby nowego mechanizmu; tylko usunęłoby
formalny błąd koniunkcji. Branch jest zamknięty jako źródło architektury, a
historyczny K pozostaje bez reinterpretacji.

# SEARCH SPACE CONTRADICTIONS

Rozważono trzy real-system neighborhoods:

1. **Uczenie prolongation/coarse space dla sparse PDE systems.** Greenfeld et
   al. (2019) nauczyli jeden mapping dla 2D diffusion, a Luz et al. (2020)
   rozszerzyli ideę na anonimowe grafy sparse SPD/SPSD i raportowali transfer
   po rozmiarze, topologii i rozkładzie. Samo `learned prolongation` nie jest
   więc nową tezą.
2. **Adaptive precision.** Trójprecyzyjne iterative refinement ma klasyczne
   warunki zbieżności i error guarantees. Bez mierzalnego modelu konkretnego
   sprzętu learned allocator byłby zależny od wall-time albo powielałby
   condition-based controller. Ten kierunek odrzucono przed aparaturą.
3. **Klasyczny adaptive/recycled preconditioning.** AlphaSA odkrywa smooth
   components bez geometrii, adaptive AMG recykluje coarse space między
   problemami, a ogólne preconditioner recycling aktualizuje wcześniejszy
   preconditioner. Zatem discovery, locality, reuse i malejący setup cost nie
   są same w sobie podpisem uczenia.

# SELECTED CAUSAL THESIS

Wybrana teza brzmi:

> Jeden source-identical learner, obserwujący wyłącznie anonimowy graf
> numerycznej sparse matrix i dozwolone residual transcripts, może nauczyć
> lokalną regułę budowy lub korekty prolongation/coarse space, która przenosi
> się z wielu realnych rodzin aplikacyjnych na jakościowo niewidziane rodziny
> i rozmiary, a przy certyfikowanym residual/error zmniejsza pełny koszt
> prospective sequence of solves względem per-instance adaptive SA/AMG oraz
> classical preconditioner/coarse-space recycling.

Czynnikiem przyczynowym nie jest `GNN`, `AMG` ani lepsza convergence rate.
Jest nim **transfer wcześniej nauczonej, anonimowej lokalnej reguły poza
rodziny źródłowe, ponad to co odzyskuje adaptacja i recycling z bieżącej lub
poprzedniej macierzy**. Efekt nie może pochodzić z nazw PDE, geometrii, grup
SuiteSparse, ręcznie podanego near-nullspace, kolejności pobrania ani
benchmark-specific feature engineering.

# NON-EQUIVALENCE BOUNDARY

Teza jest naukowo różna od wcześniejszych NEXTAI experiments, bo wynik ma być
certyfikowany na realnych sparse linear systems, a uczonym obiektem jest
transferowalna reguła konstrukcji solver state. Nie jest jednak automatycznie
różna od klasycznej adaptacji. Dlatego wynik jest evidence tylko wtedy, gdy
jednocześnie:

- `shared` przewyższa source-identical `independent` przy tym samym core,
  stałych, pojemności i dozwolonych danych;
- `cross-family-only` przewyższa `support-only` na każdej held-out application
  family, bez użycia family IDs;
- adaptive SA/AMG, standard AMG, recycled coarse-space/preconditioner i
  frozen/no-learning mapping są mocnymi obowiązkowymi kontrolkami;
- sukces zachodzi przy dopasowanym residual lub solution error, a nie tylko
  przy surrogate loss albo convergence factor;
- pełny koszt obejmuje data acquisition, meta-fit, hierarchy/setup, query,
  update, sparse operations, bytes touched, state, peak memory i workload
  horizons co najmniej R1/R4/R16;
- efekt występuje na co najmniej trzech skalach i nie pogarsza worst-family;
  wymagany podpis to non-increasing iteration growth poza train size oraz
  dodatni, zamrożony break-even horizon.

Zwycięstwo tylko nad Black-Box AMG, tylko wewnątrz jednej klasy diffusion albo
tylko w convergence factor jest causal-equivalent do znanego prior art i nie
zmieni confidence projektu.

# WHY THE RESULT WOULD CHANGE BELIEF

Pozytywny wynik pod powyższą granicą byłby pierwszym w NEXTAI dowodem, że
source-identical rule learned from observations wnosi informację użyteczną na
nowych jakościowo realnych rodzinach ponad per-instance classical discovery i
reuse, przy exact external correctness certificate. Uderzałby jednocześnie w
RC2, RC4 i RC7.

Negatywny quick zamknąłby dokładną tezę `shared anonymous prolongation transfer
beyond adaptive/recycled AMG`; nie wolno byłoby ratować jej zmianą depth,
width, message-passing rounds, loss, aggregation ani matrix subset po wyniku.
To czyni przyszły quick belief-changing również przy wyniku negatywnym.

# PROSPECTIVE DATA BOUNDARY

Jedynym wybranym kandydatem datasetu jest publiczna SuiteSparse Matrix
Collection. Zawiera realne sparse matrices z wielu domen, format Matrix Market
i CC-BY 4.0; należy zachować oryginalne matrix metadata i citations. W tym
cyklu nie pobrano żadnych danych i nie wybrano macierzy po wyniku.

Przyszły service-only acquisition musi zamrozić przed learnerem ograniczony
corpus square SPD/SPSD systems z co najmniej trzema realnymi application
groups i trzema skalami. Group labels mogą służyć wyłącznie evaluatorowi do
splitu i raportu; candidate ani feature pipeline nie mogą ich widzieć. Należy
z góry odrzucić singular/incompatible systems według jawnych algebraic rules,
nie po jakości kandydata.

# DEPENDENCY JUSTIFICATION

Repozytorium ma NumPy i Torch, lecz nie ma SciPy ani PyAMG. Rzetelny test
wymaga mocnych, niepisanych pod kandydata implementacji AMG i sparse Krylov
operations. Lokalna implementacja alphaSA/recycling byłaby duża, ryzykowna i
mogłaby sztucznie osłabić najważniejszą kontrolkę.

Proponowana pojedyncza zależność to `pyamg==5.3.0` wraz z wymaganą przez nią
SciPy. PyPI publikuje CPython 3.12 Windows wheels, MIT license, source hash i
maintained AMG implementations. Zależności **nie zainstalowano**. Zgodnie z
AGENTS.md instalacja czeka na osobną, jawną zgodę użytkownika. Nie proponuje
się żadnego zewnętrznego modelu, API ani orchestration service.

# OBSERVATION / INTERPRETATION / UNCERTAINTY

**OBSERVATION:** learned prolongation, adaptive near-nullspace discovery i
preconditioner reuse mają bezpośredni prior art. SuiteSparse oraz PyAMG dają
realny corpus i mocne klasyczne kontrolki, ale nie są obecnie częścią projektu.
RID ma legalną klasyczną CCA prawie exact.

**INTERPRETATION:** jedynym niezdeduplikowanym pytaniem w tym neighborhood jest
cross-application amortized transfer ponad adaptive i recycled controls. Nie
wolno interpretować samego learned AMG jako nowego mechanizmu.

**UNCERTAINTY:** źródła nie dowodzą, że żaden opublikowany system nie testował
dokładnie wszystkich wymaganych cross-application/full-cost ablations. Część
SuiteSparse matrices może nie mieć odpowiednich right-hand sides lub może być
niezgodna z jednym solver family; to musi rozstrzygnąć prospective data audit,
nie selekcja post-result. Realna przewaga kosztowa może zależeć od compiled
kernels i hardware, dlatego operation/byte accounting pozostaje primary, a
wall time diagnostic.

**CONFIDENCE:** wysokie (`0.90`), że RID nie powinien być dalej rozwijany;
wysokie (`0.88`), że plain learned prolongation jest zduplikowanym prior art;
umiarkowane (`0.67`), że ostrzejsza teza cross-family transfer beyond
adaptive/recycling jest wykonalna i rzeczywiście rozstrzygająca.

# DECISION

`SELECT_REAL_SPARSE_PDE_SHARED_PROLONGATION_THESIS_PENDING_DEPENDENCY_APPROVAL`.

Experiment ID: brak (`SEARCH MODE`). Immutable plan path: brak. Decyzja nie
zmienia evidence ani confidence żadnej formalnej hipotezy, nie inkrementuje G1
i nie autoryzuje scoringu.

Dokładny następny dozwolony krok, po jawnej zgodzie na zależność, to jeden
service-only wake: zainstalować i zahashować `pyamg==5.3.0` plus SciPy, pobrać
lokalnie licencjonowany i bounded prospective subset SuiteSparse z pełnymi
metadanymi, wykonać audit SPD/SPSD/scale/application split oraz udowodnić, że
adaptive SA/AMG i recycling są uruchamialnymi controls. Nie wolno w tym kroku
tworzyć HYP, planu, seeda, kandydata ani scoringu. Dopiero pozytywny audit może
prowadzić do prerejestracji jednego quicka tej dokładnej tezy.
