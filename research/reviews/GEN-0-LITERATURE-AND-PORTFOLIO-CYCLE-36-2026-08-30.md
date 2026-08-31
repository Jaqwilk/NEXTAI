# GEN-0 — przegląd literatury i portfolio, cykl 36

Zakres: obowiązkowy wake review-only po 35 ukończonych eksperymentach, wynikający jednocześnie z kadencji literaturowej co 6 i refleksji co 12 cykli. Obejmuje EXP-0030–0035. Nie utworzono planu, nie zmieniono benchmarku ani kodu kandydatów i nie wykonano scoringu. Dodano pięć źródeł pierwotnych `SRC-0088–SRC-0092`.

## 1. Czego obiektywnie się nauczyliśmy?

- EXP-0030: z surowych historii action-observation można odzyskać wystarczający predictive quotient bez latent labels. CSSR/bisimulation były exact; contrastive state i information bottleneck odtworzyły tę samą partycję przy odpowiednio `12.55%` i `13.07%` większym workload, a mały recurrent był mniej zdolny.
- EXP-0031: adaptacyjna liczba kroków jest wartościowa, gdy wspólny transition jest drogi. Tani transition-internal gate obniżył workload o `29.40%` względem fixed-max, ale osobny learned halt dodał `17.74%` workload bez zmiany zdolności lub liczby kroków.
- EXP-0032: learned VSA router poprawił cleanup względem prostego bucketu, lecz jedna noisy komórka spadła do `0.9167`; exact tuple store był `74,236.5x` tańszy w query i `65,329.1x` w workload. Nawet oracle routing pozostał ponad cztery rzędy wielkości droższy w query.
- EXP-0033: learned parallel factor relaxation dał autentyczny query-level counter-signal: exact transfer na niewidziane codewords, near-zero K slope, jedna runda i `24.69%` mniej query ops niż exact affine decoding. Pełny workload był jednak `21.45x`, stan `13.26x`, a update `11.27x` większy; dynamika była klasycznym równoległym parity bit-flipping.
- EXP-0034: sparse event NCA była `19.68x` tańsza w query niż dense NCA i zachowała recurrent local memory oraz repair, lecz exact finite-state propagation miało identyczną zdolność przy `46.22x` niższych query ops i `28.10x` niższym workload.
- EXP-0035: brak jawnych entity IDs nie uniemożliwił stałego query cost. Analytic paired-stability hash osiągnął exact behavior i K slope `0`, będąc `182.69x` tańszy w query niż exact probabilistic scan. Contrastive hash osiągnął tylko `0.5417` cold i `0.5208` near accuracy.
- Najmocniej zreplikowana zasada jest implementacyjna: po opłaceniu reprezentacji indeks, predictive quotient, transition gate, event queue albo skompilowany factor graph mogą ograniczyć pracę query do aktywnego problemu. Nie zreplikowała się niedominowana learned metoda pozyskania takiej reprezentacji.
- Wszystkie wyniki nadal pochodzą z zamkniętych, widocznych mikrosystemów. Nie ma podstaw do twierdzenia o następcy LLM, otwartym świecie ani nowym prawie skalowania.

## 2. Które założenia zostały sfalsyfikowane?

- „Brak latent ID” nie wystarcza jako test automatycznego odkrywania reprezentacji. Dostarczone pary, finite-memory bias, pełne lokalne atomy albo regularna rodzina kodów mogą nadal przekazywać ontologię w innej formie.
- Learned parametrization nie stanowi osobnej zasady, gdy po fit jest równoważna CSSR, spectral factorization, convergence gate, centroid index, parity-check decoder lub finite-state table.
- Near-zero query K slope nie dowodzi lepszej pełnej ekonomii. Fit, raw-input pass, state, update albo discovery regularnie przenosiły koszt poza query.
- Równoległość i event-driven execution są prawdziwymi źródłami oszczędności względem dense/sequential controls, ale nie są z natury neuralne ani nowe.
- Większa pojemność VSA kupiona wymiarem nie jest efektywnością; koszt cleanup i codebooku może dominować nawet przy oracle routerze.
- Obecne szybkie learned controls nie uzasadniają wniosku, że bardziej rozbudowana sieć „na pewno” wygra. Taka sieć zmienia koszt i musi być oceniona jako nowy system, a nie darmowa poprawka.

## 3. Które wyniki się zreplikowały?

- Sześć razy powtórzyła się pełnosystemowa dominacja lub dokładne zrównanie przez klasyczny control przy dopasowanej zdolności.
- W EXP-0030, 0033, 0034 i 0035 lokalna praca query była niemal niezależna od nieistotnego K po zbudowaniu zwartej struktury.
- W EXP-0031 i 0034 aktywne/adaptacyjne wykonanie istotnie pokonało dense lub fixed-max execution. To utrzymuje hipotezę, że compute może śledzić aktywną trudność, ale nie rozwiązuje kosztu reprezentacji.
- EXP-0033 jest jedynym z sześciu testów, w którym learned route pokonał exact control na jednej ważnej osi query przy pełnej poprawności; efekt nie przetrwał R16 accounting.
- Nie ma dodatniej learned przewagi powtórzonej między rodzinami, na wielu seedach i po zmianie task family. Jedyny screen w tej szóstce, EXP-0032, nie przeszedł wszystkich capability gates.

## 4. Czy portfolio utknęło w jednej rodzinie?

Tak na poziomie pytania, mimo różnorodnych nazw. EXP-0030–0035 zmieniały reprezentację powierzchniową, lecz każda kohorta posiadała małą dokładną strukturę, którą learner mógł odzyskać, a następnie porównać z control znającym tę samą klasę struktury. To jest dobry sposób falsyfikowania fałszywej nowości, ale zły generator nieskończonej serii odkryć.

Portfolio ma dwanaście hipotez, z których jedenaście jest dormant, a jedyną aktywną jest sceptyczna HYP-0012. Pozostawienie jej jako głównego generatora eksperymentów prowadziłoby do confirmation bias: projekt budowałby kolejne światy, w których klasyczny algorytm z definicji istnieje. HYP-0012 pozostaje obowiązkową dyscypliną accounting, ale nie może wybierać następnej rodziny.

Następny test powinien zmienić rodzaj transferu: nie tylko nowe przykłady w tej samej latentnej algebrze, lecz ta sama użyteczna operacja widziana przez niezgodne symbole i reprezentacje wykonawcze.

## 5. Czy optymalizujemy implementację zamiast zasady?

Ryzyko jest wysokie. Dalsze strojenie recurrent encoder, ACT, VSA dimension/router, factor discovery, NCA indicator rule lub contrastive hash jest zabronione przez ich analizy. Dodatkowe warstwy mogłyby poprawić toy score, ale nie odpowiedziałyby na główną lukę: skąd bierze się semantycznie przenośna operacja, gdy nazwy, kody i składnia się zmieniają?

Najlepszym dawnym sygnałem, który nie został jeszcze przetestowany w ten sposób, jest HYP-0002. EXP-0007–0009 stabilnie odkrywały makro i obniżały deep search, ale DSL, prymitywy i ich semantyka były stałe. Wznowienie ma sens wyłącznie jako cross-representation transfer; czwarty within-DSL extractor byłby optymalizacją implementacji.

## 6. Jaki wynik najbardziej zmieniłby przekonania?

Najbardziej informacyjny byłby learner, który z kilku domen wykonawczych odkrywa tę samą operację na poziomie zachowania, a w nowej domenie z opaque tokenami i permutowanym stanem:

- identyfikuje operację z ograniczonej liczby surowych trace probes, bez latent IDs i ręcznego mapowania symboli;
- zachowuje exact lub prerejestrowaną bezpieczną accuracy na niewidzianych kompozycjach;
- zmniejsza liczbę search nodes i średni inference workload względem primitive enumeration;
- pokonuje semantic canonicalization, graph matching, MDL/anti-unification i hierarchical Bayesian controls po policzeniu alignment, discovery, fit, state i update;
- zbliża się do oracle-library lower bound, zamiast logicznie niemożliwego wymagania „pokonania oracle”;
- replikuje transfer na wielu seedach i co najmniej dwóch held-out algebrach przed statusem promising.

Negatywny wynik też byłby wartościowy: pokazałby, że wcześniejsza kompresja biblioteki zależała od wspólnego ręcznie podanego DSL, czyli dokładnie od brakującego mostu reprezentacyjnego.

## 7. Która wcześniejsza praca zawiera pozorną nowość?

| Pozorna nowość | Prior art | Konsekwencja testowa |
|---|---|---|
| Joint library growth i learned search | EC² (`SRC-0088`) oraz DreamCoder (`SRC-0009`, `SRC-0041`) | Within-domain Explore-Compress-Compile nie jest nowością; trzeba zmienić reprezentację domeny. |
| Współdzielenie fragmentów między zadaniami | Hierarchical Bayesian programs (`SRC-0089`) | Obowiązkowy probabilistyczny/MDL control bez neural guidance. |
| Odporność biblioteki na różną składnię | BABBLE/e-graph anti-unification (`SRC-0090`) | Sam rename lub rewrite nie dowodzi learned semantic transfer. |
| Język jako scaffold abstrakcji | LAPS (`SRC-0091`) | Language supervision może przenosić ontologię; parser/encoder i adnotacje muszą być policzone. |
| LLM-guided synthesis plus symbolic compression | LILO (`SRC-0092`) | To silny hybrydowy poprzednik, ale zewnętrzny LLM jest niedozwolony i nie może wykonywać alignment za darmo. |
| Szybka czysta kompresja korpusu | Stitch (`SRC-0013`) | Compressivity trzeba oddzielić od held-out capability i kosztu użycia. |

Literatura wskazuje, że nowość nie leży w samym odkrywaniu makr. Potencjalnie odróżniające pytanie to tani transfer wykonawczej semantyki bez wspólnej składni, latent ID, language teacher lub zadanej teorii równości.

## 8. Który następny test ma największą oczekiwaną informację?

Warunkowo reaktywować HYP-0002 bez zmiany confidence i przed scoringiem przeprowadzić osobny prior-art/design gate dla `behavioral_conjugacy_library_transfer_v1`.

### Minimalna kohorta

- Światy: kilka treningowych DSL i jeden held-out DSL realizują tę samą małą algebrę transformacji, ale mają niezależne opaque nazwy tokenów oraz niezależną permutację reprezentacji stanów. Pojedyncze prymitywy są celowo niejednoznaczne; dopiero relacje kompozycji rozróżniają poprawne mapowanie.
- Dane: surowe transition traces i rozwiązane programy treningowe; brak latent primitive IDs, wspólnego codebooka, ręcznej teorii równości i zewnętrznego modelu. Target udostępnia ograniczony, jawnie płatny zestaw probes.
- Zadanie: odkryć reprezentację makra invariant względem zmiany nazw i koniugacji stanu, a następnie użyć jej do syntezy niewidzianych target programs przy D=`1/4/6` i rosnącej liczbie nieistotnych programów K=`8/32`.
- Kontrole: random, primitive exhaustive enumeration, exact trace memo, syntactic library reuse, semantic canonicalization/graph matching, MDL lub anti-unification, hierarchical Bayesian library, learned relational alignment, oracle primitive correspondence i oracle minimal library.
- Accounting: raw trace/probe reads, alignment comparisons, search nodes, execution ops, library discovery, fit, state, target update, retention oraz R1/R16 workload. Każdy control używa tej samej specyfikacji i enumeratora po alignment.
- Kill: learned alignment poniżej `0.95` w dowolnej komórce, false transfer, zależność query od K, brak lokalnego update lub zdominowanie przez semantic canonicalization/MDL przy dopasowanej zdolności pozostawia HYP-0002 dormant bez strojenia.
- Dodatni quick: exact transfer w każdej komórce, near-zero query K slope i niższy pełny amortized workload niż wszystkie nieoracle controls. Quick pozwala tylko na screen; status promising wymaga trzech seedów i nowej held-out algebry.

To pytanie jest mocniejsze niż pierwotne `held_out_dsl_library_transfer_v1`, ponieważ rename nie wystarcza: reprezentacja stanów także się zmienia, a klasyczne semantic matching jest jawnie najsilniejszym nullem. Jeśli design gate wykaże, że target probes deterministycznie przekazują pełne mapowanie albo że oracle criterion jest logicznie niemożliwy, nie prerejestrować benchmarku; następną opcją jest nowa hipoteza object-centric causal decomposition zamiast naprawiania HYP-0002.

## Decyzja portfolio

- HYP-0002: `testing` wyłącznie jako wybór jednego cross-representation quick, confidence pozostaje `0.54`; nie jest to nowe pozytywne evidence.
- HYP-0012: pozostaje `testing` jako reguła pomiaru, lecz confidence spada z `0.84` do `0.80`. Sześć kolejnych klasycznych nulli wzmacnia wynik lokalny, ale jednorodność widocznych syntetycznych generatorów i konstrukcja kontroli nie uzasadniają rosnącej wiary w uniwersalny lower bound.
- Pozostałe rodziny pozostają dormant. Nie stroić żadnego benchmarku EXP-0030–0035.
- Po review następny wake może wykonać design gate i najwyżej jeden prerejestrowany quick. Ten cykl nie uruchamia eksperymentu.
