# GEN-0 review po cyklu 12 — 2026-08-30

Zakres: obowiązkowy cykl refleksji po 12 ukończonych eksperymentach. Nie utworzono planu, nie zmieniono benchmarku ani nie wykonano scoringu. Ledger zawiera 66/66 ukończonych przebiegów kandydatów; jedyny błąd był niepunktowanym wyścigiem monitora przed EXP-0003, po którym ten sam plan wykonano bez zmiany.

## 1. Czego obiektywnie się nauczyliśmy?

- Lokalny dostęp może mieć empiryczny K slope `0`: pokazały to jawny indeks, event queue i factorized causal execution. W każdym przypadku query otrzymywało jednak identyfikatory lub strukturę umożliwiającą routing.
- Globalny scan/cleanup ujawniał koszt K: linear scan miał slope około `1`, VSA `0.992`, synchronous CA `1.54`, a dense causal execution `0.79–1.02`.
- Warunkowe wykonywanie nie jest samo w sobie przewagą. Learned halt kosztował średnio `40` operacji wobec `16` dla dokładnego fixed-max; oracle sharding `14` wobec `7` dla bezpośredniego indeksu.
- Exact-repeat memo obniżyło warm query do jednej operacji, ale nie wykazało transferu abstrakcji ani lokalnej invalidacji. Program library nauczyła się właściwego makra i ograniczyła głęboki search, lecz nie spełniła pełnego progu amortyzacji dla D=4 i została zdominowana przez oracle.
- Interventional invariance było najmocniejszym uczonym mechanizmem: w EXP-0012 osiągnęło accuracy/OOD `1.0` w 36 komórkach i trzech seedach, podczas gdy ablacja bez etykiet interwencji miała `0.0833`. Local execution miało K slope `0`, lecz fit wzrósł do `3.46M` operacji i oracle dawał to samo wykonanie bez kosztu uczenia.

## 2. Które założenia zostały sfalsyfikowane?

- Sparse activation, adaptive depth, moduły, cache i event scheduling nie są samodzielnymi zasadami następcy LLM; klasyczny indeks, BFS, fixed-depth lub oracle wyjaśniały ich korzyść taniej.
- Binding/unbinding bez lokalnego routingu nie skaluje pojemnościowo.
- Exact cache nie jest doświadczeniową kompilacją rozumowania, a kompresja biblioteki nie gwarantuje pełnej amortyzacji.
- Dokładność na typowym length split nie może być jedynym testem algorytmu; prior art `SRC-0024` pokazuje awarie na rzadkich symetrycznych wejściach.

Nie sfalsyfikowano całych rodzin ACT, VSA, NCA, causal learning ani learned machines. Odrzucono konkretne mechanizmy i silne interpretacje na lokalnych kohortach.

## 3. Które wyniki się zreplikowały?

- Indexed K slope `0` i dokładne D-local traversal: EXP-0001/0002.
- Exact-repeat cache: trzy seedy EXP-0002.
- Wybór makra i redukcja głębokiego search: EXP-0007/0008/0009; jednocześnie EXP-0008 wykazał błąd identyfikowalności, a EXP-0009 go potwierdził przez korektę specyfikacji.
- Causal OOD composition i lokalny K slope `0`: EXP-0011/0012, w tym adversarialny screen i ablacja.

Nie ma jeszcze replikacji między różnymi rodzinami zadań ani ślepego holdoutu.

## 4. Czy portfolio utknęło w jednej rodzinie?

Tak, na wyższym poziomie abstrakcji. Nazwy zmieniły się z grafu przez DSL i komórki do przyczynowości, ale wszystkie 12 eksperymentów to małe deterministyczne światy z jawnymi encjami, skończonym zestawem prymitywów i lokalnym symbolicznym oracle. Dziewięć eksperymentów przypada na trzy blisko powiązane serie po trzy. Nie testowano uczenia instrukcji, nieznanej reprezentacji, surowej percepcji ani transferu algorytmu między domenami.

## 5. Czy optymalizujemy implementację zamiast zasady?

Ryzyko jest obecnie wysokie. Kolejny wariant causal learnera z ukrytym targetem zwiększyłby realizm, ale nadal eksploatowałby ten sam schemat: odkryj jawne lokalne mechanizmy, potem wykonaj ancestry traversal. Nie należy teraz stroić causal pools, cache, wymiaru VSA, haltera ani biblioteki DSL. HYP-0001 staje się kontrolą dormant, HYP-0011 traci priorytet, a HYP-0008 pozostaje wynikiem do późniejszego transferu, nie następnym eksperymentem.

## 6. Jaki wynik najbardziej zmieniłby obecne przekonania?

Mały uczony kontroler musiałby z demonstracji odkryć wielokrotnie używane instrukcje, złożyć je w niewidziany program i wykonać dokładnie na dłuższej oraz adversarialnej pamięci. Aktywna praca powinna rosnąć z liczbą wykonanych instrukcji, nie z K, a pełny rachunek musi objąć ślady nadzoru, fit, stan, dostęp do pamięci i próg amortyzacji. Porażka memorizer/control na tej samej kompozycji jest konieczna; jawnie przekazany program nie jest wynikiem uczenia.

## 7. Gdzie prior art zawiera pozorną nowość?

| Pozorna nowość | Prior art | Konsekwencja |
|---|---|---|
| Uczony kontroler z pamięcią zewnętrzną | NTM i DNC (`SRC-0005`, `SRC-0006`) | Sam hard/soft memory access nie jest nową architekturą. |
| Wspólny interpreter, pamięć programów i kompozycja podprogramów | Neural Programmer-Interpreters (`SRC-0022`) | Pełne execution traces trzeba rozliczyć jako silny nadzór; lokalny wynik nie byłby nowością. |
| Szeroka ocena uczonych algorytmów | CLRS (`SRC-0023`) | Jeden pointer task jest screenem mechanizmu, nie dowodem ogólnego algorytmicznego rozumowania. |
| Length generalization | Neural GPU i analiza jego ograniczeń (`SRC-0024`) | Wymagany jest oddzielny adversarial-pattern split, nie tylko losowe dłuższe wejścia. |

## 8. Następny test o największej oczekiwanej informacji

Priorytetem jest dotąd nieprzetestowana HYP-0009, nie dalsza eksploatacja HYP-0008. Następny cykl może zaproponować wersjonowaną kohortę `pointer_machine_composition_v1`; ten review jej nie tworzy.

### Minimalny test rozstrzygający

- Mała pamięć wskaźnikowa z K nieistotnymi komórkami oraz kilkoma prymitywnymi instrukcjami read/move/write/branch.
- Trening wyłącznie na krótkich śladach i pojedynczych prymitywach; test na niewidzianych kompozycjach, większym D oraz osobnym zbiorze rzadkich symetrycznych wzorców.
- Kontrole: random, exact trace memorizer, dense/soft-access recurrent scan, uczony hard-pointer controller i symboliczny oracle interpreter.
- Metryki: exact i adversarial accuracy, composition/length OOD, K/D slopes, memory accesses, controller/trace fit ops, state bytes, update cost i amortyzacja dla jawnego workloadu.
- Sygnał dodatni quick: exact held-out composition i adversarial accuracy, K slope bliski `0`, wyraźna przewaga capability nad memorizerem oraz znacznie mniej memory accesses niż dense/soft scan. Dopuszcza to screen, nie status `promising`.
- Sygnał ujemny: sukces wymaga etykiety gotowego programu, znika na nowej kompozycji lub symetrii, dostęp staje się gęsty w K albo koszt uczenia nie amortyzuje się wobec bezpośredniego interpretera.

Kontrakt kodu: jeden mały generator, jeden jawny interpreter i najwyżej po jednym minimalnym kandydacie na rozstrzygającą kontrolę; NumPy/stdlib, bez frameworka, zależności i zduplikowanych warstw. Po teście przejść do innej rodziny lub transferu, zamiast stroić pointer task.

## Decyzja portfelowa

- Żadna hipoteza nie przechodzi do `promising` ani `promoted`.
- HYP-0008 zachowuje najsilniejszy lokalny dowód uczonego mechanizmu, lecz transfer latentny zostaje odroczony o co najmniej jeden radykalnie inny test.
- HYP-0009 dostaje najwyższy priorytet informacyjny bez wzrostu confidence; literatura nie jest wynikiem lokalnym.
- HYP-0012 pozostaje obowiązkowym pełnym rachunkiem kosztów dla każdego dodatniego wyniku.
