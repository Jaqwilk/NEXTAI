# Zewnętrzny audyt programu NEXTAI — 2026-09-03

## Status tego dokumentu

- Typ: append-only przegląd zewnętrzny na prośbę użytkownika; rola audytora
  „Principal Research Scientist / research director”.
- Nie jest wynikiem eksperymentu, nie zmienia żadnego planu, wyniku, analizy,
  zdarzenia hipotezy, benchmarku, manifestu ani konfiguracji. Nie tworzy
  hipotezy, planu, seeda ani scoringu. Nie zwiększa okna `G1-POST-EXP-0059-V1`.
- Zakres lektury: `docs/ORIGINAL_MANIFEST.md`, `README.md`, `docs/ROADMAP.md`,
  `docs/OCENA_POMYSLU.md`, `docs/SCIENTIFIC_PROTOCOL.md`, `docs/PRIOR_ART.md`,
  `docs/METRICS.md`, `AGENTS.md`, `program.md`, `config/research.toml`,
  `research/state.json`, `research/experiments.tsv`,
  `research/hypothesis_events.jsonl`, `research/events.jsonl`, przeglądy
  strategiczne cykli 226–282, analizy near-missów
  (`EXP-20260830-0009/0016/0033`, `EXP-20260831-0007/0008`,
  `EXP-20260901-0036/0041/0042/0044/0056`), `CAL-20260901-0001`, oraz
  statystyki kodu (`src/`, `tests/`).
- Trzy poziomy twierdzeń są rozdzielone: **OBSERWACJA (repo)**,
  **INTERPRETACJA**, **SPEKULACJA / PROPOZYCJA**.
- Uwaga techniczna: `uv run nextai doctor` na czystym checkoucie Linux zwraca
  `FAIL` (manifest integralności nie zgadza się z trzema chronionymi plikami
  przy czystym `git status`; `REPORT.md` „stale”). Nie zmienia to wniosków
  naukowych, ale oznacza, że zamrożona integralność nie jest odtwarzalna z
  samego Gita na innej platformie (sekcja Y).

---

## A. Rekonstrukcja historii

**OBSERWACJA (repo)**

- Cały program trwał ok. 80 godzin zegarowych: pierwsze zdarzenie
  `2026-08-30T00:00Z`, ostatnie `2026-09-02T08:15Z`. 282 cykle, mediana ok.
  17 minut na cykl. Dwugodzinny interwał heartbeatu został usunięty na
  polecenie użytkownika w 12. godzinie (`events.jsonl`, 2026-08-30 11:57).
- 99 ukończonych eksperymentów: 131 planów, z czego 119 `quick` (1 seed) i 12
  `screen` (3 seedy); ukończonych screenów 11; `deep` — zero.
- 59 hipotez: 36 `falsified`, 22 `dormant`, 1 `testing`. Jedyną `testing` jest
  HYP-0012 (sceptyczna hipoteza pełnego kosztu), której pewność urosła z 0.50
  do 0.88.
- Aparat: ok. 39k LOC, 100 modułów benchmarków, 518 plików kandydatów, 117
  plików testów, 228 przeglądów (ok. 156k słów), 99 analiz (ok. 82k słów), 423
  źródła; `SCIENTIFIC_PROTOCOL.md` ma 1266 linii, bo dopisywano do niego
  kontrakty kolejnych wersji kohort (v2…v13).
- Tylko 4 z 518 plików kandydatów importują `torch`. Typowe „learned”
  kandydaty to ręcznie napisane estymatory numpy o szerokości 16–32, 24–32
  epok, budżet 180 s CPU na kandydata, K zwykle 8/32.

Chronologia z rzeczywistymi punktami zwrotnymi:

1. **G0 (EXP-0001–0035, ok. 9 h)** — świat następników/grafu: indeks, cache,
   VSA, ACT-halting, routing; potem program library (HYP-0002), causal DAG
   (HYP-0008), energia (HYP-0007), NCA (HYP-0006). Realny pivot
   metodologiczny: protokół v2 po cyklu 36.
2. **G1-A (EXP-0038–0059, 30.08)** — czterorodzinna synthetic cross-family
   transfer z „lossless serializer” i anonimizacją. Tu wprowadzono wymóg
   source-identical/cross-family (zdarzenie 2026-08-30 12:22). Realny pivot
   pytania badawczego.
3. **G1-B (30.08 wieczór – 31.08)** — dane realne: DronePropA, N-CMAPSS,
   Causal Chambers WT, trzy rodziny ciągłe. Realny pivot: „real tasks”.
4. **G1-C (31.08 – 01.09)** — breadth scouts: bajty repozytorium, masked
   infilling (13 wersji), WT (5 wersji), whole-I/O search (5 wersji), cellular
   (6 wersji), addressing (3 wersje). Nie są to pivoty: ok. 90% to ten sam
   causal intervention („naucz selektor/adres/stan i porównaj z
   frozen/shuffled/klasycznym”) pod nową nazwą roli (cykl 226 sam to
   stwierdza).
5. **Cykle 226–228** — okno G1 (8 slotów), kalibracja `CAL-20260901-0001`.
6. **Cykle 234–238** — reset strategiczny na polecenie użytkownika; audyt
   założeń A1–A14; synteza porażek RC1–RC7 → U1/U2/U3. Jedyny realny pivot
   epistemiczny: od szukania mechanizmu do teorii bottlenecków.
7. **Cykle 239–242** — próby zbudowania dyskryminatora dla U1
   (`BRIDGE-U1-U2-V1`, `RID-CONTRACT-001`); obie zawiodły przed scoringiem.
8. **Cykle 243–247, EXP-20260902-0001** — SuiteSparse prolongation, ostatni
   wynik, negatyw.
9. **Cykle 248–282** — SEARCH MODE: „conditional information-boundary
   exhaustion” (cykl 261), następnie ok. 25 kolejnych cykli monitoringu
   literatury biologicznej, każdy zakończony `CLOSE_…` z pewnością 0.995 i
   „exact next search” wskazującym kolejny organizm. Zero scoringu, zero
   zmiany przekonań.

**INTERPRETACJA**

Program miał trzy prawdziwe pivoty (protokół v2, cross-family/source-identical,
real data) i jeden pivot epistemiczny (U1/U2/U3). Reszta ruchu — ok. 60 cykli
„service-only successor vN” i ok. 30 cykli SEARCH MODE — to zmiany nazw
mechanizmów lub dokumentów przy stałym pytaniu przyczynowym. Ostatnia faza jest
degeneracją: aparat naukowy przekształcił się w filtr literatury z siedmioma
bramkami skonstruowanymi tak, że nic nie przechodzi.

---

## B. Czym NEXTAI jest naprawdę; goal drift

**OBSERWACJA (repo)**

- Manifest (§1, §14, §29–30): cel to `capability / inference cost`, sygnatura
  `∂C/∂K → 0`, `C ∝ useful work`, decoupling wiedzy od obliczeń. Wymagania
  architektoniczne: brak („TARGET PROPERTIES … NOT architectural
  requirements”).
- Brama G1 (`AGENTS.md`, `ROADMAP.md`): observation-learned + source-identical
  + causal gain vs frozen/klasyczny control + ≥2 rodziny + unseen operation +
  3 seedy + adversarial + local signature + full-cost Pareto (R1/R4/R16) + brak
  ontologii/privileged support/preprocessingu — jednocześnie.
- Manifest §21 podaje „relies on human-written ontology” jako kryterium utraty
  priorytetu. Manifest §13: „never reject a radically different prototype
  merely because the first implementation is inelegant”. Program wybrał regułę
  przeciwną: „A negative ends that exact mechanism without post-result tuning”.

Klasyfikacja wymagań:

| Wymaganie | Klasa | Uzasadnienie |
|---|---|---|
| pełny koszt end-to-end, bez ukrywania pracy | konieczne (manifest §15) | bez tego cel nie jest mierzalny |
| matched capability | konieczne | manifest §2 |
| brak ręcznej ontologii niosącej rozwiązanie | konieczne w słabej formie | manifest §21; nie „brak jakiejkolwiek struktury interfejsu” |
| replikacja + wariant adwersarialny przed promocją | użyteczna heurystyka | manifest §19; nie „jeden adversarial innego zadania zamyka rodzinę” |
| observation-learned | heurystyka | ostrzejsze niż dla rywala (LLM uczy się z supervised next-token) |
| source-identical między ≥3 anonimizowanymi rodzinami | arbitralna preferencja NEXTAI | dodana 30.08 12:22 |
| „genuinely different mechanism”, negatyw zamyka, zakaz iteracji | arbitralna, sprzeczna z manifestem §13 | zabija co-adaptację |
| horyzont R1/R4/R16 jako granica amortyzacji | arbitralna | manifest mówi o amortyzacji, nie o 16 użyciach |
| causal gain vs shuffled/frozen source-identical ablacji | użyteczna heurystyka | dobra dla atrybucji, zła jako warunek konieczny |
| nowość względem prior art („not a recognizable research direction”) | arbitralna (instrukcja użytkownika, cykl 236) | manifest §26: „Do not abandon an idea merely because a related concept exists” |

**INTERPRETACJA**

Drift ma trzy warstwy: (1) „capability per inference cost” → „learned candidate
musi pobić dokładny klasyczny algorytm po pełnym koszcie na K≤32 przy R16”;
(2) „decoupling wiedzy od obliczeń” → „source-identical transfer między
anonimowymi rodzinami”; (3) heurystyki metodologiczne wpisane do `AGENTS.md`
jako prawa egzekwowane przez kod. Punkt, w którym heurystyka stała się prawem:
zdarzenie 2026-08-30 12:22 (transfer_protocol jako schema-mandatory) i cykl 227
(okno G1 z conjunction 10 warunków).

---

## C. Co zostało odkryte

**OBSERWACJA (repo)** — regularności powtarzające się w wielu kohortach:

1. **RC2** (cykl 237): na małych zamkniętych generatorach learned system albo
   zbiega do klasycznej statystyki wystarczającej, albo jest przez nią
   zdominowany po pełnym koszcie. Ok. 40 eksperymentów.
2. **RC5**: lokalność/rzadkość oszczędza dopiero po posiadaniu poprawnego
   adresu/stanu; „K-slope ≈ 0” jest tanie (każdy indeks) i nie jest trudną
   częścią problemu. Najbardziej przenośny wniosek programu.
3. **RC3**: frozen/shuffled ablacja często wygrywała z uczoną wersją; mierzone
   na learnerach szerokości 16–32.
4. **Pozytyw replikowany**: learned pushdown (`EXP-20260901-0041/0042`):
   144/144 exact spans, 3 seedy, korpus rozłączny plikami i hashami,
   głębokości 3–5 z treningu ≤2; ablacja depth-two 0/144; najlepszy klasyczny
   control 0.035.
5. **Pozytyw replikowany**: WT recurrent residual (`EXP-20260831-0006/0007`):
   NRMSE 0.673 vs 1.007 najlepszego controla, margines 2.5× progu, H96
   ekstrapolacja z fit H32, Pareto-nondominated po pełnym koszcie.
6. **Kalibracja `CAL-20260901-0001`**: transformer na GPU 2.9·10¹¹ „work units”
   w 0.48 s; PPM 9.9·10⁷ w 1.72 s. Licznik operacji przewiduje odwrotność
   rzeczywistego czasu z błędem ok. 4 rzędów wielkości.
7. Learned causal factorization (`EXP-0015/0016`): exact recovery i exact OOD
   composition 36/36; pełny K-slope 0.61 wyłącznie z kosztu percepcji.
8. Warm reuse (`EXP-0002/0023/0024`, `EXP-20260901-0003/0021`): realne, tylko
   przy stabilnym kluczu.

**INTERPRETACJA**

- `mechanism failed`: 36 „falsified” dotyczy dokładnych reguł na dokładnych
  kohortach — uczciwe i dobrze udokumentowane.
- `research direction weakened`: „learn a small selector and compare with
  frozen/classical” — słusznie osłabione (cykl 226 pkt 4).
- `fundamental principle probably false`: nic w repo nie uzasadnia tego
  poziomu. Cykl 261 („conditional information-boundary exhaustion”) i cykl 236
  („routing/addressing/sparse memory: closed”) to nadgeneralizacja z
  1-seedowych quicków learnerów o kilkuset parametrach, 180 s CPU, K≤32. Cykl
  237 sam zastrzega „Confidence <0.20 dla ekstrapolacji … na skalę LLM”, a
  kolejne 40 cykli zachowywało się, jakby ekstrapolacja była pewna.

Czego wiemy więcej niż bez NEXTAI: (a) „K-independent query cost” jest
trywialny i nie powinien być kryterium promocji; (b) w mikroświatach z
zamkniętym generatorem klasyczny control zawsze ma przewagę informacyjną;
(c) learned stan rekurencyjny potrafi ekstrapolować głębokość z bardzo małych
danych (pushdown, WT) — sprzeczne z RC6 jako regułą ogólną; (d) liczniki
operacji nie są kosztem.

---

## D. Re-audyt near-missów

**1. HYP-0028 — WT bounded recurrent residual** (`EXP-20260831-0006/0007/0008`)

- OBSERWACJA: replikowany, duży efekt, Pareto-nondominated, H96 ekstrapolacja.
  Analiza 0007 pisze: „cannot separate the causal contribution of recurrence
  from slot-local RLS”. Następnym testem był jednoseedowy quick pooled learner
  na trzech anonimizowanych, zero-paddowanych rodzinach fizycznych (turbofan,
  dron, syntetyczny event). Negatyw → `dormant`. Analiza 0008 pisze:
  „Heterogeneous normalization and channel geometry may make one dense affine
  slow state unsuitable across these families.”
- INTERPRETACJA: odrzucony z niewłaściwego powodu. Test nie dyskryminuje
  hipotezy o rekurencji; dyskryminuje wymóg cross-family. Właściwe następne
  testy: (i) ablacja recurrence-off/RLS-on; (ii) drugi układ tej samej klasy;
  (iii) DMDc/VAR+RLS jako control. Żaden nie został wykonany. Jedyne w repo
  pełnokosztowe, replikowane pobicie mocnych klasycznych adaptacyjnych controli
  na danych realnych.

**2. HYP-0050 — learned pushdown** (`EXP-20260901-0041/0042/0044`)

- OBSERWACJA: pozytyw replikowany na korpusie rozłącznym. Wariant adwersarialny
  v13 zmienił zadanie (rekonstrukcja wewnętrznych pushów z widocznego łańcucha
  returnów, wymagająca inferencji wstecz) dla learnera zbudowanego do emisji
  closerów lewo-prawo. 0/144. Analiza 0044 pisze: „V13 tests inverse push
  reconstruction rather than the closure emission named in the original
  hypothesis”. Decyzja: `discard`, `dormant`.
- INTERPRETACJA: to inny benchmark, nie wariant adwersarialny mechanizmu.
  Poprawny wniosek: „learner jest jednokierunkowym stack executorem”. Success
  gate („reusable operator”) był bramą G2/G3, nie G1. Re-Pair/PPM „tańsze” przy
  0–3.5% exact spans — matched-capability control nie istniał.

**3. `EXP-20260830-0033` — parity energy** (HYP-0007)

- OBSERWACJA: learner z nieoznaczonych codewords odzyskał dokładnie 651
  faktorów parity-check graph, naprawa 6 błędów w jednej rundzie, identyczny z
  oracle. Zdominowany przez `exact_affine_span_decoder`, który wie, że dane są
  kodem afinicznym.
- INTERPRETACJA: „learned generalist vs hand-engineered specialist”.
  Rekonstrukcja znanego algorytmu z danych potraktowana jako porażka, choć
  manifest §22 wymienia „automatic discovery of reusable operations” jako
  kryterium promocji.

**4. `EXP-20260901-0036` — learned search ordering** (HYP-0047)

- OBSERWACJA: meta-ordering R1 7.15×, R4 2.73×, R16 1.35× kosztu frozen.
  Liniowa ekstrapolacja z zapisanych R1/R4/R16 (stały deficyt fit ok. 2.5M ops,
  oszczędność ok. 0.05M/użycie) daje przecięcie ok. R≈50–55. Zabity na R16.
- INTERPRETACJA: artefakt arbitralnego horyzontu.

**5. `EXP-20260830-0015/0016` — learned causal factorization** (HYP-0008)

- OBSERWACJA: 1.0 w 36/36 komórkach, exact OOD composition, zero wariancji
  seedów. „Nie na Pareto”, bo dominował oracle z zerowym kosztem fitu (protokół
  v1).
- INTERPRETACJA: decyzje G0 podejmowano na podstawie dominacji przez oracle;
  błąd naprawiony w v2, nigdy nie odwrócony dla HYP-0008.

Wspólny wzorzec: pozytyw → wariant adwersarialny zmieniający zadanie albo
wymagający transferu G3/G4 → negatyw → „negatyw zamyka mechanizm”. Nie jest tu
proponowany rescue-tuning. Proponowana jest zmiana przekonań: repo zawiera dwa
replikowane dowody, że learned stan rekurencyjny/stosowy ekstrapoluje głębokość,
i jeden dowód, że pełnokosztowe pobicie klasycznych adaptacyjnych controli na
danych realnych jest możliwe — a ledger zapisuje te fakty jako `dormant` z
pewnością 0.20.

---

## E. Fairness: learned vs classical

**OBSERWACJA (repo)**

- Kontrole „implementable”: `exact_affine_span_decoder` (zna klasę kodu),
  `specialist_contextual_chow_liu_suite` na natywnych widokach (kandydat widzi
  anonimowe tokeny), `enumerative_mdl_vm` (zna DSL), `raw_balanced_kd_tree` na
  surowej geometrii syntetycznej, CSSR, `timed_automaton_matcher`,
  `certified_decision_tree` z podanym codebookiem. Kandydat: source-identical,
  anonimizowany, bez etykiet rodzin, z opłaconym fitem.
- Koszt projektowania controla nie jest liczony.
- Cykle 239–242: agent sam nie potrafił zbudować świata, w którym relacja
  niesie informację niedostępną klasycznemu controlowi (ridge stopnia 2
  rozwiązał BRIDGE; spektralny control zawalił RID).

**INTERPRETACJA**

Asymetria jest systematyczna. Kontrole są wymagane, by wykryć, że generator sam
dostarcza strukturę, ale wynik został zinterpretowany jako dowód przeciw learned
computation zamiast jako dowód, że benchmark ma wbudowaną statystykę
wystarczającą.

**PROPOZYCJA — information budget parity**

1. Każdy control deklaruje bity wiedzy o klasie problemu (description length
   specyfikacji). Control z niezerową wiedzą klasy jest raportowany jako
   `class-informed lower bound`, nie jako implementable rywal.
2. Implementable rywal = algorytm klasyczny generyczny na tym samym anonimowym
   interfejsie, bez wiedzy o klasie.
3. Trzeci koszyk: mały model neuronowy trenowany gradientowo o matched
   parametrach — rzeczywisty rywal programu.

---

## F. False negatives

**OBSERWACJA (repo)**

- 119/131 planów `quick` (1 seed). 0 `deep`. 180 s CPU/kandydat, 1.5 GB RAM.
  K zwykle 8/32; K≥1000 w 7 planach.
- Priory: pewność początkowa 0.03–0.20 (HYP-0048: 0.04; HYP-0057: 0.03;
  HYP-0046: 0.06). Posterior po negatywie 0.01–0.02. Jedyna hipoteza z
  rosnącą pewnością to HYP-0012 (null).
- Reguły: jeden quick per mechanizm, negatyw zamyka, zakaz tuningu, następny
  mechanizm „genuinely different”. Brak drugiej iteracji dla jakiejkolwiek
  idei.
- Brak kontroli pozytywnej: w 99 eksperymentach nie ma ani jednego, w którym
  znany dobry learned system został przepuszczony przez bramki G1, by zmierzyć
  ich czułość. Jedyny transformer (`CAL-20260901-0001`) trenował 0.68 s.

**INTERPRETACJA**

False positives ≈ 0, ale czułość aparatu na prawdziwe pozytywy jest
niezmierzona i prawdopodobnie bliska zeru. Pipeline produkujący wyłącznie
negatywy bez kontroli pozytywnej jest nieinterpretowalny. J-curve wykluczona
regułą R16; co-adaptacja wykluczona regułą one-factor + no-iteration; skala
wykluczona budżetem 180 s CPU. NEXTAI jest zoptymalizowany do zabijania idei i
sam to raportuje (cykl 236: „another architecture scoring would be an alias
sweep”).

---

## G. Primitive-first vs system-first

**OBSERWACJA**: manifest §23 przewiduje kombinowanie zwycięzców. Repo zawiera
trzy zasady z realnymi sygnaturami (lokalny stan rekurencyjny/stosowy z
ekstrapolacją głębokości; slot-local update z bounded state; exact
fallback/indeks). Nigdy nie zbudowano systemu z więcej niż jedną. Cykl 256:
„Combining those unrelated successes would … violate the one-factor policy”.

**INTERPRETACJA**: one-factor-at-a-time jest właściwą jednostką atrybucji, nie
odkrycia. Hipoteza interakcji jest nietestowana, nie sfalsyfikowana.

**PROPOZYCJA**: system-first jest teraz bardziej uzasadniony, ale tylko po
kontroli pozytywnej (F) i sprzętowym koszcie (J). Ablacje po działającym
systemie, nie zamiast niego.

---

## H. Construct validity mikroświatów

**OBSERWACJA**: generatory (permutacje 31 stanów, 256 programów, 144 stany, kod
afiniczny rangi 6, 7-symbolowa gramatyka, 4-kanałowy ring CA) mają małą
dokładną strukturę odzyskiwaną w całości przez klasyczny control. Dane realne
anonimizowane do poziomu niszczącego semantykę; rozmiary: WT test = 2 pliki,
masked infilling = 3 pliki testowe; zero-padding heterogenicznych wymiarów.
Cykle 239–242: agent nie zdołał skonstruować mikroświata z relacyjną przewagą.

**INTERPRETACJA**: ekologia benchmarków selekcjonuje przeciwko systemom, których
przewaga pojawia się w noisy high-dimensional worlds, długich historiach
adaptacji i długich horyzontach reuse.

**PROPOZYCJA**: jedna realna klasa zadań (V) jako główny plac boju; mikroświaty
wyłącznie jako narzędzia atrybucji efektów zaobserwowanych na realnym zadaniu.

---

## I. Koszt i horyzont amortyzacji

**OBSERWACJA**: granica acquisition+discovery+fit+verification+update+state+
maintenance+query, horyzonty R1/R4/R16; R256/R4096 tylko w entity addressing.
`EXP-20260901-0036`: przecięcie ok. R50; `EXP-0033`: „próg amortyzacji
tysiące zapytań”. Reguła: wybór horyzontu po wyniku = tuning.

**INTERPRETACJA**: program przeszedł od „czy po nauczeniu system wnioskuje dużo
taniej” do „czy lifetime cost jest lepszy już przy 16 użyciach”. Analogiczna
miara dla LLM (pretraining ÷ 16 zapytań) byłaby absurdalna. Właściwa granica
dla następcy LLM: koszt marginalny zapytania przy matched capability plus koszt
marginalny aktualizacji wiedzy; discovery raportowane jako krzywa break-even.

**PROPOZYCJA**: metryką pierwszorzędną staje się prerejestrowany R\* (horyzont
przecięcia) z przedziałem ufności; brama: „R\* ≤ zadeklarowany realistyczny
workload dla klasy zadań” (dla zadań LLM-owych 10⁶–10⁹).

---

## J. Cost metrics vs sprzęt

**OBSERWACJA**: `CAL-20260901-0001`: transformer 2943× więcej „work units” niż
PPM i 3.6× krótszy czas; przepustowość 115k B/s vs 32k B/s. Wynik oznaczony
„systems diagnostic, not evidence” i nigdy nie użyty do korekty modelu kosztu.
Wszystkie 99 decyzji Pareto używa ops/bytes touched.

**INTERPRETACJA**: oś kosztu w każdym froncie Pareto jest niezwalidowana, a
dla porównań „sekwencyjny algorytm wskaźnikowy vs gęsta równoległa algebra”
prawdopodobnie odwrócona. Klasyczne controle (PPM, CTW, k-d tree, CSSR, MDL)
są klasą algorytmów faworyzowaną przez liczniki operacji i karaną przez GPU.
RC2/RC4 mogą być w części artefaktem miary.

**PROPOZYCJA**: przejście do pomiarów sprzętowych teraz: koszt = zmierzony czas
i energia na zadeklarowanym sprzęcie (GPU i CPU dla obu stron), liczniki jako
metadane. Lokalny RTX 4070 i `torch 2.6+cu124` działają.

---

## K. Metodologia statystyczna

**OBSERWACJA**: 88% wyników z jednego seeda. Progi zamrażane ad hoc per
kohorta. Brak analizy mocy. Język pewności: „0.995 in hashes and completion”,
„0.99 that the preregistered conjunction failed” — pewność co do mechaniki
bramek, nie co do twierdzeń naukowych. W SEARCH MODE 0.995 w każdym z ok. 25
cykli. Seedy w WT screen zmieniają tylko permutację kanałów (CV 10⁻¹⁵).

**INTERPRETACJA**: winner’s curse nie zachodzi. Ryzyko, że wiele 1-seedowych
negatywów przy learnerach o kilkuset parametrach to false negatives, jest
wysokie i nieoszacowane. System deklaruje 0.99 dla „bramka nie przeszła” i
traktuje to jak 0.99 dla „mechanizm nie działa”.

**PROPOZYCJA**: (1) każda bramka ma zmierzoną czułość na kontroli pozytywnej;
(2) estymaty efektu z CI zamiast binarnych bramek; (3) sekwencyjna reguła stopu
zamiast „jeden negatyw zamyka”; (4) osobne słownictwo: „gate-fail confidence”
vs „mechanism-false posterior”.

---

## L. Proces generowania hipotez

**OBSERWACJA**: ten sam kontekst pisze hipotezę z pewnością 0.04, projektuje
kryterium zabicia, implementuje „minimalnego” kandydata, interpretuje i wybiera
następny mechanizm. Każda interwencja użytkownika (30.08, 31.08, 01.09)
natychmiast zmieniała kierunek całego programu.

**INTERPRETACJA**: bias strukturalny — agent, który zaraz ogłosi „negatyw
zamyka mechanizm”, ma bodziec do niskich priorów i minimalnych implementacji.

**PROPOZYCJA**: role w osobnych kontekstach z zaślepionymi artefaktami:
PROPOSER/ADVOCATE (buduje najsilniejszą uczciwą wersję), SKEPTIC (kontrole i
ablacje, nie widzi implementacji przed zamrożeniem), STATISTICIAN (seedy, moc,
próg, R\*; nie zna hipotezy), INTERPRETER (wyniki bez etykiet ról), PRIOR-ART
REVIEWER (po pozytywie, nie przed testem).

---

## M. Incentives i process hacking

**OBSERWACJA**:

1. „Exact next discriminating action” → cykl 282 kończy się poleceniem audytu
   fuzji komórkowej *Physarum*; 281 pszczoły; 280 móżdżek; 279 mapa poznawcza.
2. Append-only + review co cykl → 228 przeglądów, protokół 1266 linii.
3. „Never more than two consecutive no-scoring cycles” → 13 wersji masked
   infilling, 6 repo compression, 6 cellular: scoring dla scoringu.
4. „Negatyw zamyka bez tuningu” + „genuinely different” → bodziec do niskich
   priorów i minimalnych implementacji.
5. SEARCH MODE z 7 bramkami nieprzechodzalnymi dla żadnej publikacji →
   gwarantowane `CLOSE_…` z pewnością 0.995 = zero informacji na cykl.
6. HYP-0012: jedyna hipoteza z rosnącą pewnością jest hipotezą zerową.

**PROPOZYCJA — cel agenta**: nagroda = oczekiwana zmiana przekonań (np. KL
między priorem a posteriorem) na stałej liście pytań programowych
(`research/BELIEFS.json`). Cykl bez zmiany przekonań ≥ ε jest kosztem. Twarde
reguły: maks. 1 cykl literaturowy na 5; zakaz nowej bramki bez kontroli
pozytywnej; zakaz „exact next action” bez oszacowanego expected information
gain.

---

## N. Ciężar epistemiczny repo

**OBSERWACJA**: 156k słów przeglądów, 82k analiz, 97 KB protokołu-changelogu,
100 modułów benchmarków, 518 kandydatów, `REPORT.md` 174 KB z „Pareto axes
unavailable” dla kohort v1. Cykl 236 musiał w jednym kontekście streścić 98
wyników, 58 hipotez, 101 analiz, 183 przeglądy, 224 źródła.

**PROPOZYCJA** (bez usuwania historii):

- `research/raw/` — obecne plany/wyniki/analizy/events, niezmienne;
- `research/CAUSAL_MAP.md` — ≤2 strony: interwencje × kohorty × wynik;
- `research/BELIEFS.json` — pytania programowe z jawnymi prawdopodobieństwami
  i datą ostatniej zmiany (szkic dołączony w tym commicie);
- `research/BRANCHES.md` — rejestr mechanizmów: status, powód zamknięcia, co by
  go otworzyło;
- `research/NEGATIVES.tsv` — skompresowane negatywy;
- `research/OPEN_QUESTIONS.md`, `research/WATCHLIST.md`;
- `docs/SCIENTIFIC_PROTOCOL.md` ≤ 300 linii; kontrakty kohort →
  `benchmarks/<name>/CONTRACT.md`.

---

## O. Roadmapa G0–G8

**OBSERWACJA**: brama G1 wymaga jednocześnie unseen operation (G3), ≥2 rodziny
(G3/G7), local update (G5), full-cost Pareto przy K-scaling (G4), adversarial
(Phase H).

**PROPOZYCJA**: re-definicja bram, nie nowa roadmapa. G1 = „mechanizm ma
replikowaną sygnaturę jakościową na jednym realnym zadaniu przy matched
capability i zmierzonym koszcie sprzętowym”. HYP-0028 i HYP-0050 przechodzą tak
zdefiniowany G1 i powinny wejść do G2/G3 jako komponenty systemu.

---

## P. Empiria → teoria

**OBSERWACJA**: U1/U2/U3, RC1–RC7, taksonomia kanałów (cykl 261), kontrakty
BRIDGE/RID — materiał na twierdzenie: „jeżeli generator należy do klasy, dla
której control ma obliczalną statystykę wystarczającą, żaden
observation-learned kandydat nie może być Pareto-nondominated po pełnym koszcie
przy skończonym horyzoncie”.

**INTERPRETACJA**: to niemal tautologia. Wartość leży w kierunku odwrotnym:
warunki, w których learned structure może wygrać: (a) klasa generatora nieznana
lub statystyka wystarczająca nieobliczalna, (b) horyzont reuse ≫ koszt
discovery / oszczędność per query, (c) sprzęt faworyzuje gęstą równoległość.

**PROPOZYCJA**: jedna nota teoretyczna (≤10 stron) z trzema konjekturami i
warunkami falsyfikacji; nie program dowodowy.

---

## Q. 99 eksperymentów jako meta-dataset

**OBSERWACJA**: metryki heterogeniczne, 88% jednoseedowych, brak wspólnego
effect size. Rozkład hipotez (cykl 261): 34 target-local fit/update, 19
transfer, 5 search credit. Zero eksperymentów z siecią >10⁵ parametrów, zero na
GPU, zero z językiem, zero kontroli pozytywnej, jeden z K×100 dla learned
kandydata.

**INTERPRETACJA**: ilościowa meta-analiza nie jest identyfikowalna; jakościowa
mapa (237/261) istnieje. Blind spoty są widoczne bez modelu.

---

## R. Opportunity cost i racjonalność ex ante

- G0 (35 eksperymentów, 9 h): racjonalne ex ante.
- Czterorodzinny synthetic cross-family z anonimizacją (EXP-0041–0057):
  wątpliwe ex ante; po drugim negatywie kontynuacja (v3, v4, v5) niska
  informacyjnie.
- Real data: racjonalne; anonimizacja i zero-padding do wspólnego tensora — nie.
- 13 wersji masked infilling / 6 repo compression: nieracjonalne ex ante po
  drugim negatywie tej samej interwencji.
- Kalibracja sprzętowa: racjonalna, zignorowana.
- SEARCH MODE 248–282: zero informacji ex ante.

Kontrfaktyczny program (80 h, RTX 4070, Codex): (1) 5 h kontroli pozytywnej;
(2) 10 h sprzętowego modelu kosztu; (3) jedno realne zadanie z K-scaling;
(4) 30 h system-first vs matched transformer z ablacjami; (5) 20 h replikacji i
adversarial na pozytywach.

---

## S. Blind spots

1. Brak kontroli pozytywnej / kalibracji czułości bramek.
2. Rywal nigdy nie wszedł na arenę: jedyny transformer trenował 0.68 s w
   kalibracji; nigdy nie porównano learned kandydata z małym transformerem/SSM
   o matched parametrach na GPU.
3. Interakcje i realna capability: zero systemów z >1 zasadą, zero kontaktu z
   językiem, planowaniem, kodem.

Klasy strukturalnie nieproponowalne przez harness: wszystko, co wymaga >180 s
CPU, >1.5 GB RAM, GPU, pretrainingu, lub czego przewaga ujawnia się po >16
użyciach.

---

## T. Czy szukać jednej „fundamentalnie nowej” zasady?

Ranking wg oczekiwanej wartości naukowej:

1. System-level architecture ze znanych komponentów (WT-recurrence,
   pushdown-state, slot-local update, exact index) vs matched transformer.
2. Hardware/software co-design / scaling-law discovery.
3. Theoretical result (P).
4. Nowa kombinacja prymitywów (pokrywa się z 1).
5. New learning dynamics.
6. Jedna nowa prymitywa — najniższa.
7. Zakończenie framingu — nie teraz; framing nie został przetestowany, tylko
   jego karykatura.

---

## U. Bias „fundamentally different from LLM”

**OBSERWACJA**: HYP-0010 `dormant` z uzasadnieniem „the system remains a
neural model”; cykl 236 odrzuca PDE adaptive computation jako „recognizable
research direction”; cykl 235 odrzuca neural processes jako „renaming”.

**INTERPRETACJA**: manifest §5 wprost pozwala na sieci neuronowe i Transformery
jako komponenty. Właściwa granica: nowość mierzy się sygnaturą skalowania
(∂C/∂K, C vs D, koszt aktualizacji), nie genealogią mechanizmu.

---

## V. Język i realna capability

**OBSERWACJA**: zero kontaktu z językiem, planowaniem, kodem jako zadaniem.
Najbliższe: bajty własnego repozytorium (3 pliki testowe).

**PROPOZYCJA**: najwcześniejszy moment to teraz. Minimalny benchmark:
byte-/small-token-level korpus tekstu z kontrolowanym zbiorem faktów rosnącym
×10/×100 i pytaniami wymagającymi 1–4 kroków kompozycji; kontrola pozytywna:
mały transformer i mały SSM na GPU; koszt mierzony sprzętowo.

---

## W. Stop criteria dla programu

Zakończyć framing, jeżeli wszystkie trzy zachodzą:

1. Po naprawie bramek najlepszy system-first kandydat przy matched capability
   nie pokazuje na 3 skalach K i 2 klasach zadań krzywej kosztu sprzętowego o
   mniejszym nachyleniu niż transformer baseline;
2. Żadna sygnatura (ekstrapolacja głębokości, lokalna aktualizacja bez
   retrainingu) nie replikuje się na realnym zadaniu językopodobnym;
3. Przewaga kosztowa znika przy pomiarze na GPU.

Nie kończyć na podstawie: kolejnych negatywów 1-seedowych, wyczerpania nazw
mechanizmów, literaturowych filtrów.

## X. Upside triggers

Którykolwiek z: matched capability z ≥3× niższym zmierzonym czasem/energią na
GPU na 3 skalach K z przewagą rosnącą z K; replikowana (≥3 niezależne źródła
danych) ekstrapolacja głębokości/kompozycji na realnym zadaniu, gdzie matched
transformer zawodzi; lokalna aktualizacja wiedzy bez retrainingu z retencją ≥
transformer + fine-tuning przy 10× niższym koszcie aktualizacji; R\* < 10³ dla
mechanizmu z pozytywem w dwóch klasach zadań.

## Y. Niezależna ślepa ewaluacja

**OBSERWACJA**: `doctor` na czystym checkoucie zwraca FAIL (integrity mismatch
trzech chronionych plików). Niezależna reprodukcja zatrzymuje się w kroku 0.

**INTERPRETACJA**: obecnie nie ma czego ślepo ewaluować. Hidden evaluator ma
wartość, gdy jeden kandydat przejdzie bramki zwalidowane kontrolą pozytywną na
dwóch zadaniach. Wcześniej: naprawić odtwarzalność manifestów między
platformami.

---

## Z. Decyzja

### 1. Decyzja strategiczna

Zatrzymać obecną pętlę autoresearch (okno G1, SEARCH MODE, monitory
literatury) i przebudować laboratorium, nie porzucając grand objective.
Jednostka badań: primitive → mały kompletny system. Oś kosztu: liczniki
operacji → pomiar sprzętowy. Bramki skalibrowane kontrolą pozytywną. Dwa
near-missy (HYP-0028, HYP-0050) wracają jako komponenty, nie jako hipotezy do
rescue-tuningu.

### 2. Dlaczego

- Brak kontroli pozytywnej w 99 eksperymentach → negatywy nieinterpretowalne.
- `CAL-20260901-0001`: oś kosztu odwrócona o ok. 4 rzędy wielkości.
- `EXP-20260831-0007` i `EXP-20260901-0042`: dwa replikowane pozytywy zamknięte
  testami, które zmieniły zadanie lub wymagały transferu G3/G4.
- Cykle 239–242: agent nie potrafi skonstruować mikroświata, w którym uczenie ma
  szansę.
- Cykle 248–282: pętla produkuje artefakty o zerowej zmianie przekonań.

### 3. Pierwsze pięć działań

1. Kalibracja czułości bramek kontrolą pozytywną (mały transformer i SSM na GPU
   na zadaniu, gdzie ich przewaga nad PPM/CTW jest ustalona).
2. Sprzętowy model kosztu: zmierzony czas i energia dla wszystkich istniejących
   controli i dwóch pozytywów; regresja ops→czas per klasa algorytmu.
3. Ablacja WT, której nie zrobiono (recurrence-off/RLS-on; DMDc/VAR+RLS) plus
   drugi układ fizyczny tej samej klasy, jeden screen.
4. System-first prototyp: learned recurrent/pushdown state + slot-local update
   + exact index z fallbackiem, na jednym realnym zadaniu językopodobnym z
   K×10/×100, vs matched transformer, koszt sprzętowy, R\* jako metryka;
   ablacje po działającym systemie.
5. Redesign pętli agenta: role (L), cel = zmiana przekonań (M), struktura repo
   (N), odtwarzalność manifestów (Y).

### 4. Czego nie robić

- Kolejnych „service-only successor vN” i roli-only wrapperów.
- Cykli literaturowych typu SEARCH MODE; monitorów biologicznych.
- Nowych mikroświatów z zamkniętym generatorem jako pierwszego testu.
- Kolejnych 1-seedowych quicków learnerów szerokości 16–32 przeciw dokładnym
  solverom.
- Bramek z „source-identical między ≥3 anonimowymi rodzinami” jako warunkiem G1.
- Rozbudowy protokołu, manifestów, schematów przed działaniem 5.
- Prób „nowej fundamentalnej prymitywy” wybranej przez filtr nowości nazwy.

### 5. Stop condition dla proponowanej ścieżki

Porzucić redesign, jeżeli: (a) kontrola pozytywna przechodzi bramki, a mimo to
system-first prototyp na dwóch klasach zadań i trzech skalach K nie ma ani
jednej sygnatury lepszej niż matched transformer; oraz (b) ablacja WT pokaże,
że efekt to RLS. Wtedy program przechodzi do trybu teoretycznego (P) albo
zostaje zamknięty.

### 6. Success trigger

Prototyp z działania 4 przy matched capability ma zmierzony koszt sprzętowy o
nachyleniu względem K mniejszym niż transformer na 3 skalach, replikowany na 3
seedach i 2 klasach zadań, z R\* < 10³, i sygnatura utrzymuje się po jednym
wariancie adwersarialnym tego samego zadania.

---

## AA. Odpowiedzi na pytania końcowe

1. **Bliżej alternatywy dla LLM?** Bliżej co do wiedzy o metodzie (czego nie
   mierzyć; dwa fakty o learned stanie rekurencyjnym), nie co do architektury.
   Aparat, jak sam dokumentuje, nie może już wyprodukować pozytywu.
2. **Odkrył / wyeliminował intuicje / zbudował system odrzucania?** Trzecie z
   domieszką drugiego. Czułości systemu nigdy nie zmierzył.
3. **„Knowledge capacity decoupled from inference compute”?** Źle postawiona w
   wersji operacyjnej: „query cost niezależny od K” jest trywialne; „uczony
   system znajduje właściwy fragment bez skanowania” jest tożsame z problemem
   reprezentacji i nie było testowane na skali, na której ma sens.
4. **Najsilniejsze ograniczenie?** Economics of measurement + metodologia: oś
   kosztu niezwalidowana, bramki nieskalibrowane, jednostka badań niezdolna do
   wykazania przewagi.
5. **Pytanie, które należało zadać wcześniej?** „Czy nasze bramki przepuściłyby
   mały transformer na zadaniu, na którym wiemy, że wygrywa?” Powinno padać w
   cyklu 36.
6. **Wynik źle oceniony?** `CAL-20260901-0001` (odłożony jako diagnostyka, a
   podważa oś kosztu wszystkich porównań). Drugi: `EXP-20260831-0007`.
7. **Ostrożność: zaleta czy ograniczenie?** Dziś ograniczenie — rygor
   jednostronny: chroni przed false positives przy nieznanym false negative
   rate.
8. **Finansować następne 6 miesięcy?** Tak, warunkowo: najpierw działania 1–3
   z sekcji Z jako tania faza rozstrzygająca. Najlepsze uzasadnienie:
   `EXP-20260831-0007` i `EXP-20260901-0042` — dwa fakty, których obecny aparat
   nie potrafił ani rozwinąć, ani prawidłowo obalić. Przy negatywie fazy
   rozstrzygającej: program o tym samym celu zorganizowany od strony rywala
   (mały transformer/SSM na GPU jako odniesienie, jedno realne zadanie z
   K-scaling, pytanie „która modyfikacja strukturalna zmienia nachylenie
   krzywej kosztu względem K”) — scaling-law discovery zamiast primitive
   discovery.
