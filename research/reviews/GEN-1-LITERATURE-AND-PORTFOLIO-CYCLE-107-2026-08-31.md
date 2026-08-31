# GEN-1 — przegląd literatury i portfolio, cykl 107

Zakres: obowiązkowy review-only wake przy 55 ukończonych eksperymentach, sześć wyników po punkcie odniesienia `completed=49`. Nie utworzono hipotezy ani planu, nie zmieniono benchmarku, evaluatora, schematu, manifestu ani kodu kandydata, nie wylosowano seeda i nie uruchomiono scoringu. Przegląd obejmuje EXP-0057, EXP-0059 oraz EXP-0001–0004. EXP-0004 pozostaje terminalnie nieważny i służy wyłącznie diagnostyce. Dodano sześć źródeł pierwotnych `SRC-0150`–`SRC-0155`.

## 1. Czego obiektywnie się nauczyliśmy?

- EXP-0057 był ważnym testem observable-equation operator algebra. Shared osiągnął `0.625` średniej, ale `0.0` minimum-combination: dokładność przeszła od `0.50/0.25/0.0` przy K=8 do `1.0/1.0/1.0` przy K=32. Jest to sygnał progu pokrycia, nie transferu przy ograniczonym wsparciu; pełny meta-fit był około `26.1×` droższy od exact MDL.
- EXP-0059 ważnie odrzucił fixed rank-12 operator subspace na DronePropA. Shared NRMSE `0.696182` przegrał z pooled RLS/no-sharing `0.655023`, a minimalne condition/trajectory gains wyniosły `-0.066055/-0.083582`. Nie wolno stroić ranku, ridge ani shrinkage.
- EXP-0001 ważnie odrzucił coordinate-aligned rank-4 transfer: DS08a był niestabilny, a cross-family-only gain był ujemny we wszystkich trzech rodzinach. Persistence był jednocześnie lepszy jakościowo i tańszy w R16.
- EXP-0002 pokazał rozdzielenie dwóch efektów. Exchangeable bounded residual shared pokonał independent w każdej rodzinie i osiągnął `0.619947` overall przy pełnej stabilności, lecz cross-family-only zaszkodził obu rodzinom mechanicznym, a worst-family był gorszy od persistence. To jest dowód same-family regularization, nie przenośnej reprezentacji.
- EXP-0003 ważnie odrzucił support-calibrated convex algorithmic prior: shared przegrał w DS08a, cross-family-only przegrał wszystkie sześć komórek, NRMSE wyniósł `173251.386` wobec `0.916580` persistence i koszt zapytań/adaptacji był większy.
- EXP-0004 nie obserwował pytania przyczynowego. Trzy role learnera i obowiązkowy random-hash control uległy tej samej awarii pustego bucketu przed pierwszą próbą. Wynik jest maszynowo wykluczony z evidence, Pareto, confidence, falsyfikacji i replikacji; HYP-0027 pozostaje bez wyniku naukowego.
- Żaden z sześciu wyników nie uzasadnia `promising`, replikacji dodatniej ani twierdzenia o nowym scaling law. Nie ma obecnie learned candidate z wieloseedowym, OOD i pełnokosztowym sukcesem.

## 2. Które założenia zostały sfalsyfikowane?

- Współdzielenie parametrów nie implikuje współdzielonego mechanizmu. Rank-12, rank-4, bounded residual i convex mixture mogą regularizować podobne światy, a równocześnie szkodzić światom obcym.
- Anonimowy wspólny tensor nie tworzy semantycznej zgodności kanałów. Brak family label nie wystarcza, jeśli generatory nie mają identyfikowalnego wspólnego czynnika.
- Legalna stabilność numeryczna nie jest zdolnością. EXP-0003 miał finite/stable rollout, lecz katastrofalny błąd.
- Dodatni shared-vs-independent gain nie jest wystarczającym dowodem transferu. EXP-0002 wymagał osobnego cross-family-only-vs-support-only kontrastu i właśnie on odrzucił interpretację transferową.
- Dokładność przy wysokim K nie dowodzi korzystnego skalowania. Skok EXP-0057 jest zgodny z pokryciem skończonej mapy i towarzyszy mu zero minimum przy K=8 oraz wysoki meta-fit.
- Hash manifestu i clean source audit nie zastępują wykonania obowiązkowej kontrolki. EXP-0004 wykrył brak real-file empty-bucket fixture.

## 3. Które wyniki się zreplikowały?

- Persistence pozostaje powtarzalnie najmocniejszym stabilnym, tanim punktem odniesienia w trzyrodzinnej prognozie. Pokonał rank-4 spectral, convex mixture i worst-family bounded residual, a jego pełny koszt był niższy.
- Obce rodziny nie dostarczyły uniwersalnego zysku: cross-family-only był ujemny we wszystkich komórkach EXP-0001 i EXP-0003 oraz w czterech z sześciu komórek EXP-0002.
- Same-family pooled information może pomagać: EXP-0002 uzyskał dodatni shared-vs-independent gain, ale efekt nie przeżył odcięcia same-family data. To replikuje potrzebę dwóch niezależnych kontrastów, nie hipotezę wspólnej reprezentacji.
- Klasyczne, prostsze modele nadal dominują learned parameter-sharing przy dopasowanej jakości i koszcie: exact MDL w EXP-0057, pooled/RLS w EXP-0059 i persistence w v1/v2.
- Żaden dodatni sygnał nie ma trzech scoring seeds. Wszystkie wnioski o znaku mechanizmu pozostają ograniczone do quick, choć duże prerejestrowane porażki uzasadniają zakończenie dokładnych wariantów bez tuningu.

## 4. Czy portfolio utknęło w jednej rodzinie?

Częściowo tak. EXP-0059 i EXP-0001–0004 kolejno testowały warianty przenoszenia dynamiki na realnych światach ciągłych: operator subspace, spectral prior, bounded residual, expert mixture i predictive index. Mechanizmy się różniły, lecz pytanie oraz cohort były prawie te same. Nie wolno po EXP-0004 przejść do kolejnego hasha, momentu, ranku lub mieszaniny.

HYP-0027 pozostaje uzasadnionym wyjątkiem tylko dlatego, że jego jedyny scored run jest nieważny, a nie negatywny. Jeden niezmieniony corrected quick po naprawie v4 może rozstrzygnąć odmienny czynnik — learned predictive binding versus matched raw/random indexing. Po nim kierunek kończy się przy wyniku negatywnym; dodatni quick może jedynie zezwolić na niezmienioną replikację.

## 5. Czy optymalizujemy implementacje zamiast zasad?

Ryzyko jest wysokie. Literatura rozróżnia mechanizm transferu od warunków jego identyfikowalności:

| Źródła | Wniosek dla NEXTAI |
|---|---|
| Task grouping i Taskonomy (`SRC-0150`, `SRC-0152`) | Relacje zadań są kierunkowe i trzeba je zmierzyć; task labels, affinity search i dodatkowe treningi są płatne i nie mogą być ręczną ontologią. |
| PCGrad (`SRC-0151`) | Ujemny pooling może wynikać z konfliktu optymalizacyjnego, ale task-separated gradients wymagają jawnej tożsamości zadania i nie są poprawką family-blind cohort. |
| Successor features i USFA (`SRC-0153`, `SRC-0154`) | Mocny transfer ma jawne założenie wspólnej dynamiki albo task descriptor. Oba muszą być odkryte z publicznych obserwacji lub zabronione. |
| DeepMDP (`SRC-0155`) | Predictive code powinien zachowywać przejścia i wielkość relewantną dla celu; dowolne momenty przyszłości nie gwarantują sufficiency. |

Wniosek: naprawa pustego bucketu jest naprawą wykonania zamrożonego testu, nie okazją do zmiany pięciu bitów, target moments, liczby bucketów, ridge, progów lub rodzin.

## 6. Jaki wynik najbardziej zmieniłby przekonania?

Najwięcej zmieniłby ważny, niezmieniony test HYP-0027, w którym learned key jednocześnie:

- pokonuje matched raw-window, matched random hash i persistence ponad zamrożony development noise floor w każdej rodzinie i K;
- ma dodatnie shared-vs-independent oraz cross-family-only-vs-support-only margins w każdej komórce;
- nie pogarsza worst-family, pozostaje stabilny i zachowuje K-independent capped query work;
- nie jest Pareto-dominated po policzeniu representation fit, index construction, support updates, state, bytes i R16.

Taki one-seed quick nie byłby sukcesem końcowym, ale byłby pierwszym lokalnym dowodem, że learned binding, a nie pooling parametrów, zasługuje na trzyseedową adversarial replication. Negatywny corrected quick zakończy dokładny pięciobitowy kierunek. Awaria kontrolki ponownie będzie wyłącznie długiem infrastrukturalnym.

## 7. Która wcześniejsza praca zawiera pozorną nowość?

- Learned task affinity i grupowanie nie są nowe (`SRC-0150`, `SRC-0152`). Nowością nie może być samo odkrycie, że nie wszystkie rodziny należy łączyć.
- Usuwanie gradient interference nie jest nowe (`SRC-0151`) i nie spełnia family-blind interface bez task identity.
- Reużywalne predictive occupancy/features z transferem nie są nowe (`SRC-0153`, `SRC-0154`); ich gwarancje zależą od wspólnej dynamiki lub opisu zadania.
- Latent predictive abstraction powiązana z bisimulation nie jest nowa (`SRC-0155`), podobnie jak CSSR, PSR, CPC, LSH i metric learning już zapisane w prior art HYP-0027.
- Ewentualna wartość NEXTAI leżałaby wyłącznie w rygorystycznym wyniku: representation learned bez task descriptor i ontologii, real OOD transfer, bounded local lookup/update oraz korzystny pełny koszt względem klasycznych kontrolek.

## 8. Który następny test ma największą oczekiwaną informację?

Najpierw jeden chroniony service-only wake do `heldout_three_family_continuous_transfer_v4`, bez hipotezy, planu, seeda i scoringu:

1. zachować v3 oraz EXP-0004 bez modyfikacji;
2. zdefiniować output-width-safe fallback dla pustego bucketu wspólny dla learned i matched-index controls;
3. dodać real-file fixture z 32 widocznymi wejściami, wymaganym wyjściem i celowo pustym wybranym bucketem;
4. wymagać ukończenia fixture przez random-hash i wszystkie cztery zamrożone role HYP-0027;
5. aktywować v4 dopiero po semantic tests, pełnym pytest, nowym preflight certificate, integrity i doctor PASS.

Dopiero kolejny wake może prerejestrować corrected quick HYP-0027 z identycznym kodem, bitami, momentami, bucket cap, ridge, progami, K=`4/6/9`, jednym runner-random seedem i kompletem kontrolek. EXP-0004 nie jest evidence ani replication parent.

## Decyzja portfolio

- HYP-0027 pozostaje `proposed` z confidence `0.10` i bez evidence IDs. Prior art wzmacnia wymagania kontrolne, ale nie zmienia confidence, ponieważ eksperyment nie został ważnie wykonany.
- HYP-0022, HYP-0023, HYP-0024, HYP-0025 i HYP-0026 pozostają zakończone w swoich dokładnych wariantach. Bez tuningu ranku, shrinkage, ridge, clip, atomów albo supportu.
- Nie tworzyć nowej hipotezy ani benchmarku. Po jednym service wake i jednym corrected HYP-0027 quick, portfolio musi wybrać inny fundamentalny kierunek, jeśli wynik będzie negatywny.
- Nie ma obecnie wyniku do replikacji lub promocji.
