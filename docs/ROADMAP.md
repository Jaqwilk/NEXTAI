# Roadmapa oparta na bramach dowodowych

Roadmapa nie jest harmonogramem obietnic. Przejście między generacjami zależy od dowodów, a nie od czasu. Codex wykonuje jeden ograniczony cykl na wybudzenie i może pozostać w danej generacji tak długo, jak wymaga tego walidacja.

## G0 — Infrastruktura

Cel: wykazać, że system pomiarowy odzyskuje znane jakościowo prawa.

Brama wyjścia:

- testy jednostkowe i `doctor` przechodzą;
- haszowany manifest ewaluacji jest stabilny;
- random control przegrywa na jakości;
- linear scan ma koszt rosnący z K;
- indexed graph ma koszt w przybliżeniu niezależny od K i liniowy w D;
- compiled/memoized pokazują oczekiwany trade-off pamięć–update–warm cost;
- awarie, timeout i integralność mają testowane ścieżki zapisu.

## G1 — Prymitywy obliczeniowe

Cel: szeroko porównać reprezentację, pamięć, routing i lokalne wykonywanie.

Minimalny portfel:

- sparse indexed memory;
- VSA/HDC;
- recurrent/adaptive-depth;
- event-driven NCA/local graph;
- memory controller / pointer machine;
- skeptic adversarial routing baseline.

Po EXP-20260901-0059 obowiązuje okno `G1-POST-EXP-0059-V1`: osiem ważnych scored eksperymentów dotyczących rzeczywiście różnych mechanizmów. Licznik startuje od zera; cykle serwisowe, błędne plany, pre-seed invalidacje i aliasy nie zwiększają go. Jeden dokładny mechanizm może otrzymać najwyżej quick, po mocnym pozytywie niezmienioną replikację oraz jeden prerejestrowany wariant adwersarialny. Negatyw kończy dokładną zasadę bez strojenia po wyniku. Przed kolejnym mikrobenchmarkiem cykl 228 wykonuje jednorazową lokalną kalibrację realnego systemu, oddzieloną od evidence kandydatów.

Brama po ośmiu wynikach wymaga co najmniej jednego uczonego z obserwacji, source-identical mechanizmu, który ma przyczynowy gain przy dopasowanej użytecznej jakości, działa w co najmniej dwóch zamrożonych rodzinach lub zadaniach i na niewidzianej operacji, przechodzi co najmniej trzy seedy i prerejestrowany wariant adwersarialny, zachowuje deklarowaną lokalną aktualizację lub inną jakościową sygnaturę, pozostaje implementowalnie Pareto-niedominowany po pełnym koszcie i nie korzysta z ręcznej ontologii, uprzywilejowanego supportu ani ukrytego preprocessingu. Jeżeli warunek nie zostanie spełniony, nowe scoringi architektoniczne zatrzymują się do strategicznego resetu uzgodnionego z użytkownikiem.

## G2 — Odkrywanie reguł i algorytmów

Cel: usunąć ręcznie wpisane operatory, które obecnie niosą rozwiązanie.

Testy: learned rewrites, program library, learned VM, discovery of variables/objects. Brama wymaga transferu operatora do held-out instancji i spadku kosztu search/inference, nie tylko wyższego fitu.

## G3 — Kompozycja

Cel: niewidziane kombinacje, nowe długości, nowe obiekty i zmienione powierzchowne symbole.

Brama: wynik utrzymuje się na kilku splitach kompozycyjnych i co najmniej dwóch rodzinach zadań, z aktualnym baseline'em neuralnym i symbolicznym.

## G4 — Skalowanie wiedzy

Cel: mierzyć K niezależnie od D, relevance i ambiguity.

Brama: przy co najmniej 100-krotnym wzroście nieistotnej wiedzy system zachowuje jakość, a cały dostęp/routing/bytes moved rośnie istotnie wolniej niż K. Osobno testuje się podobne distraktory, gdzie routing jest trudny.

## G5 — Continual learning

Cel: inserts, zmiany sprzeczne, zależności i forgetting.

Brama: koszt aktualizacji i dotknięty stan są lokalne, retention jest wysoki, a globalne constraints pozostają poprawne bez pełnego retrainingu.

## G6 — Język jako interfejs

Cel: dołączyć prosty, lokalny encoder/decoder bez dużego modelu w pętli inferencji.

Brama: paraphrases, ambiguity i generation działają przy policzonym koszcie całego interfejsu. Nauczyciel może tworzyć dane badawcze tylko jeśli nie jest wymagany podczas ocenianego zapytania.

## G7 — Zadania ogólne

Cel: wiedza, reasoning, matematyka, planowanie i kod na jawnie wybranej baterii.

Brama: matched-capability comparisons; żadnego uśrednienia, które ukrywa katastrofalną porażkę krytycznej zdolności.

## G8 — Konkurencja skalowania

Cel: porównać krzywe capability/cost z coraz silniejszymi konwencjonalnymi modelami.

Brama do określenia „kandydat na następcę”: niezależna replikacja, przewaga end-to-end przy podobnej jakości oraz brak zaniku przewagi wraz ze skalą.

## Pierwsza kolejka eksperymentów po kontroli G0

1. Zwiększyć K i dodać semantycznie podobne distraktory, aby zaatakować naiwną niezależność kosztu.
2. Zastąpić append-only update zmianą istniejącej krawędzi i zmierzyć dependency-aware invalidation.
3. Dodać binary VSA z kontrolą pamięci symbolicznej.
4. Porównać fixed recurrent z adaptive halting na rozdzielonych K i D.
5. Porównać synchronous local updates z event queue.
6. Zbudować mały program-library test z held-out kompozycjami.
7. Wykonać portfolio review; nie łączyć zwycięzców przed dowodem pojedynczych zasad.

## Stan po EXP-20260830-0035 i audycie cyklu 36

G0 zakończono po 35 wynikach. Aparatura zachowała kompletne plany, awarie i analizy oraz wielokrotnie odzyskała znane sygnatury indeksowania, aktywnego wykonania i klasycznych struktur. Nie powstał jednak żaden `promising` ani `promoted` kandydat: dodatnie efekty learned nie zreplikowały się między rodzinami, a oracle lub klasyczny matched-capability control zwykle dominował pełny workload.

Aktywna faza to `G1 / consolidation` pod protokołem v2. EXP-0036 zachowano i unieważniono bez scoringu, ponieważ ujawniał stały seed i powstał przy niezgodnym manifeście. Przed nowym eksperymentem trzeba aktywować nową kohortę, rozdzielić evaluator contract od implementacji, zamrozić pełny manifest i użyć runner-random seedów. Priorytetem jest jeden test cross-representation transfer z nowoczesnymi kontrolami; nie dalsze strojenie trzydziestu zamkniętych mikroworldów.
