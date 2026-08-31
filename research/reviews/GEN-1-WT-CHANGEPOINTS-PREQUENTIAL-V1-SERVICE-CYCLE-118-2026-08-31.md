# GEN-1 — WT changepoints prequential v1, cykl serwisowy 118

Zakres: dokładnie jeden chroniony cykl serwisowy. Nie utworzono hipotezy,
immutable planu, seeda scoringowego ani wyniku naukowego i nie uruchomiono
scoringu. Kohorta `heldout_wt_changepoints_prequential_v1` została aktywowana
dopiero po przejściu zamrożonej bramki developerskiej i pełnej walidacji.

## Zmienione mechanizmy

- Zamrożono whole-file split train 0–5, development 6–7 i test 8–9 oraz
  train-only mechaniczne rozpoznanie jednego sterowania i dziesięciu odpowiedzi.
- Publiczny kontrakt przekazuje wyłącznie anonimową, spójnie permutowaną historię,
  bieżące sterowanie, losowy slot i horyzont. Nazwy kanałów, plik, marker, czas,
  przyszłe sterowania i target są niedostępne.
- Granica wykonania ma kolejność query → pełna walidacja → read-only copy → SHA-256
  artifact → target reveal → slot-local update. Target nie jest odczytywany przed
  utrwaleniem kompletnej predykcji.
- Zamrożono K=18/36/54, fit depth/horizon 32, H=16/32/96, limit 16 MiB i pełne
  koszty acquisition/preprocess/fit/query/update/bytes/state/R1/R4/R16.
- Dodano osiem wymaganych kontrolek: persistence, pooled mean, exact control-level
  residual bank, normalized LMS, RLS, prechange transition bank, bounded replay
  cap 16 i fixed ridge FIR. Każda ma specyfikację, hash implementacji oraz
  uruchamiany pre-seed test zgodności.
- Plan schema, result schema, agregacja, Pareto, runner, CLI i doctor rozpoznają
  nową kohortę. Lokalnie widoczne test files pozostają wyłącznie screeningiem.

## Testy semantyczne i development smoke

17 małych testów sprawdza referencje kontrolek, slot-local update, twardy replay
cap, H96 ponad fit H32, spójną permutację kanałów, statyczny split, plan schema
oraz rzeczywistą kolejność query/artifact/reveal/update na pliku development.

Pierwsza próba smoke zatrzymała się przed obliczeniem outcome: wspólny `Baseline`
nie dziedziczył `CandidateBase`, więc audytowany loader odmówił uruchomienia. Nie
powstał wynik i nie zmieniono progów ani modeli. Po wyłącznie interfejsowej korekcie
powtórzono ten sam zamrożony smoke na plikach 6–7, K54/H96. Żaden baseline nie
spełnił progu saturacji NRMSE <= 0.50 i worst-file <= 0.75 przy pełnej finitości.

| kontrolka | NRMSE | worst-file | stable |
|---|---:|---:|---:|
| persistence | 1.094092 | 1.167073 | 1.0 |
| pooled mean | 0.936554 | 0.955101 | 1.0 |
| control-level bank | 0.975364 | 1.051019 | 1.0 |
| LMS | 0.992129 | 1.041591 | 1.0 |
| RLS | 0.901988 | 0.959224 | 1.0 |
| transition bank | 0.943090 | 1.013293 | 1.0 |
| bounded replay | 1.194908 | 1.260939 | 1.0 |
| ridge FIR | 0.934619 | 0.961484 | 1.0 |

Artefakt smoke: `research/checks/heldout_wt_changepoints_prequential_v1_development_smoke.json`,
SHA-256 `c135a5fb0076388c926b389049d31cac1b049fad63944f1f7ff3746633c765a6`.
Nie odczytano outcome’ów plików testowych 8–9.

## Integralność i decyzja

Pełne `355` testów przechodzi. Manifest obejmuje `521` plików; evaluator SHA-256
to `1d16aef7d6e18632528dddf1a6f70715531dc5bc53ade5e79fce8b94e9b9aa0e`.
Certyfikat preflight to
`9adb6b08975e245531e349c6a91d1bbf2db2cf56ee5c82911b3c5028d03f18bc`.
Integrity i doctor: PASS. Decyzja: `activate_for_later_preregistration`.

Confidence `0.995`, że implementacja i bramki odpowiadają zamrożonemu kontraktowi;
confidence `0.85`, że kohorta jest nietrywialnym screeningiem dla obecnych
kontrolek. Niepewność naukowa pozostaje wysoka: tylko dwa pliki development,
lokalnie widoczne dwa pliki testowe, brak naturalnego transition/length OOD i brak
dotychczasowego testu uczonego mechanizmu.

## Dokładny następny eksperyment

Dopiero następny wake może prerejestrować `EXP-20260831-0006`: jeden quick seed
dla jednego source-identical, permutation-equivariant bounded residual learnera,
który uczy z train wyłącznie wspólną lokalną regułę update i utrzymuje rozdzielny,
ograniczony fast state na anonimowy slot. Bez nazw kanałów, plików, poziomów lub
ręcznej ontologii i bez tuningu po wyniku. Porównać niezmieniony kod przy
K18/36/54 i H16/32/96 ze wszystkimi ośmioma kontrolkami. Przed seedem zamrozić
kryterium: poprawa NRMSE ponad train-only minimum meaningful effect `0.1325268421`,
brak pogorszenia worst-file/worst-transition, pełna stabilność, korzystna sygnatura
H96 ponad fit H32, slot-local update i brak Pareto dominacji po pełnym koszcie.
Jeden pozytywny quick jedynie zezwala na niezmienioną replikację; wynik negatywny
kończy dokładną zasadę bez strojenia.
