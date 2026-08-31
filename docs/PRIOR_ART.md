# Mapa prior art i granice nowości

## Wniosek

Większość pojedynczych składników manifestu ma silne poprzedniki. Potencjalna nowość nie polega więc na samych hasłach „lokalna pamięć”, „dynamiczny graf”, „reguły reakcji” albo „kompilowanie rozumowania”. Musiałaby polegać na **konkretnej, uczącej się kombinacji**, która zachowuje wysoką jakość, ma uczciwie policzony koszt końca-do-końca i wykazuje lepsze prawo skalowania w więcej niż jednym typie zadania.

ACC/SCCS jest na razie etykietą programu, a nie udowodnioną nową klasą obliczeń. Przed każdym twierdzeniem o nowości trzeba pokazać różnicę względem najbliższego poprzednika i eksperyment mierzący właśnie tę różnicę.

## Najbliższe rodziny

| Rodzina | Co już wiadomo | Co nadal byłoby istotnie nowe | Minimalny test różnicy |
|---|---|---|---|
| Retrieval i pamięć zewnętrzna | [RETRO](https://arxiv.org/abs/2112.04426) częściowo oddziela pamięć tekstową od parametrów kontrolera. | Otwarty system, którego routing, odczyty pamięci i dekoder pozostają tanie przy rosnącym K i porównywalnej jakości. | Skalować nieistotne i semantycznie mylące fakty; liczyć recall routingu, bytes touched i cały koszt zapytania. |
| Duża pamięć parametryczna | [Product-Key Memory](https://arxiv.org/abs/1907.05242) zwiększa pojemność przy rzadkim, strukturalnym dostępie. | Lepsza pełna ekonomia po doliczeniu budowy kluczy, indeksu, aktualizacji i błędów routingu. | Dopasować jakość i stan; skalować pamięć oraz podobne klucze, mierząc retrieval i bytes touched. |
| Sparse conditional computation | [Sparsely-Gated MoE](https://arxiv.org/abs/1701.06538) zwiększa pojemność przy ograniczonej liczbie aktywnych ekspertów. | Przewaga po doliczeniu routingu, ładowania ekspertów, komunikacji i nowych kompozycji. | Stałe top-k, rosnąca liczba ekspertów, OOD mieszanki umiejętności i pomiar transferu danych. |
| Kontroler z pamięcią | [Neural Turing Machines](https://arxiv.org/abs/1410.5401) i [DNC](https://doi.org/10.1038/nature20101) uczą kontroler operacji na pamięci zewnętrznej. | Stabilny trening, dyskretny/sublinear access i transfer algorytmów poza długości treningowe. | Porównać soft scan, dyskretny pointer i solver symboliczny na rosnącej pamięci oraz długości. |
| Zmienna ilość obliczeń | [Adaptive Computation Time](https://arxiv.org/abs/1603.08983) uczy zatrzymania rekurencyjnego modelu. | Koszt śledzący rzeczywistą trudność przy zachowanej jakości i bez ukrytej stałej pracy. | Oddzielić długość wejścia od koniecznej głębokości i porównać z fixed-depth. |
| Nowoczesne modele sekwencyjne | [Mamba](https://arxiv.org/abs/2312.00752) wnosi selektywny SSM i liniowe przetwarzanie sekwencji; [BLT](https://arxiv.org/abs/2412.09871) adaptuje granularność obliczeń do entropii bajtów. | Przewaga capability/cost poza ręcznie strukturyzowanym mikroworldem przy policzonym encoderze i treningu. | Matched-budget porównanie z selektywnym SSM i dynamicznym patchingiem na rzeczywistym interfejsie wejściowym. |
| Pamięć aktualizowana w inferencji | [Titans](https://arxiv.org/abs/2501.00663) uczy długoterminową pamięć w czasie testowym. | Tańsza, lokalnie walidowana aktualizacja i reuse bez globalnego uczenia oraz bez utraty jakości. | Porównać test-time update, retrieval, retention, stan i R1/R16 workload. |
| Program induction i biblioteki | [DreamCoder](https://arxiv.org/abs/2006.08381) odkrywa wielokrotnie używane abstrakcje programowe. | Samodzielnie odkryte operatory, które skracają koszt na nowych rodzinach zadań bez ręcznych prymitywów niosących rozwiązanie. | Held-out kompozycje, ablacją biblioteki, search nodes i MDL przed/po. |
| Lokalne systemy uczące się | [Growing Neural Cellular Automata](https://doi.org/10.23915/distill.00023) pokazuje globalną organizację z lokalnej reguły. | Abstrakcyjne rozumowanie z rzadką aktywacją, a nie pełnym synchronicznym sweepem siatki. | Porównać NCA synchroniczne, kolejkę zdarzeń i lokalny graf przy rosnącym nieaktywnym obszarze. |
| Reprezentacje kompozycyjne | [HDC/VSA survey](https://arxiv.org/abs/2111.06077) mapuje algebry wiązania i superpozycji. | Lepsza jakość–koszt przy uczeniu prymitywów i dużej, interferującej pamięci. | Capacity/interference curve, unseen bindings, cleanup cost oraz matched state bytes. |
| Systematyczna generalizacja | [SCAN](https://arxiv.org/abs/1711.00350) ujawnił słabości części modeli sekwencyjnych. | Wynik na nowocześniejszych, mocnych baseline'ach i wielu typach kompozycji, nie pojedynczy split. | Kilka splitów OOD, nowe rozmiary/głębokości, baseline symboliczny i neuralny. |
| Autonomiczna pętla badań | [autoresearch](https://github.com/karpathy/autoresearch) demonstruje serię zmian pod stałym budżetem. | Badanie paradygmatów z prerejestracją, wersjonowaniem benchmarku, Pareto i zachowaniem wyników negatywnych. | Audyt od planu przez hasz po wynik i odtworzenie cyklu z repozytorium. |

## Gdzie ACC/SCCS nakłada się na wcześniejsze idee

- „cząstki semantyczne” przypominają reprezentacje symboliczne, object-centric i VSA;
- „reakcje” przypominają production systems, graph rewriting, message passing i lokalne reguły CA;
- „energia/konkurencja hipotez” ma bliskie odpowiedniki w systemach energy-based i probabilistycznych;
- „persistent world” jest spokrewniony z pamięcią zewnętrzną, blackboard systems i world models;
- „skompilowana ścieżka A→D” przypomina memoizację, partial evaluation, program libraries i cache;
- „aktywuj tylko istotne fragmenty” pokrywa się z retrieval, sparse routing i conditional computation.

To nie dyskwalifikuje kierunku. Oznacza, że eksperymentalna nowość musi leżeć w zachowaniu systemu, nie w nowej nazwie.

## Obowiązkowa karta nowości przed promocją

Każda hipoteza przechodząca do `promising` lub `promoted` musi odpowiedzieć:

1. Jaki jest najbliższy mechanicznie poprzednik?
2. Co dokładnie pozostaje identyczne, a co jest inne?
3. Czy różnica dotyczy reprezentacji, uczenia, routingu, wykonywania czy rachunku kosztów?
4. Jaka ablacją usuwa nowy składnik bez zmiany reszty?
5. Która mierzalna sygnatura nie wynika automatycznie ze starej metody?
6. Czy twierdzenie przetrwa uwzględnienie preprocessingu, pamięci i aktualizacji?
7. Czy źródło jest pierwotne i czy agent przeczytał je, zamiast polegać na streszczeniu?

Maszynowy rejestr źródeł znajduje się w `research/sources.jsonl`. Ten dokument jest mapą, nie zamiennikiem lektury prac źródłowych.

## Aktualizacja po 6 eksperymentach — 2026-08-30

- [Stitch](https://arxiv.org/abs/2211.16605) pokazuje, że wydobywanie bibliotek z korpusu programów może być znacznie tańsze niż dedukcyjny komponent DreamCoder, ale jego główną miarą jest kompresja znanych programów. Następny test musi osobno mierzyć held-out search.
- [Switch Transformer](https://arxiv.org/abs/2101.03961) i [Expert Choice](https://arxiv.org/abs/2202.09368) wzmacniają sparse MoE jako baseline, lecz same prace jawnie pozostawiają koszty routingu, komunikacji i dużego stanu.
- [Routing Networks](https://arxiv.org/abs/1711.01239) są wcześniejszym przykładem dynamicznej kompozycji bloków funkcyjnych. HYP-0010 może być nowa tylko przez lepszą sygnaturę transferu/kosztu, nie przez sam router.
- [How Modular Should Neural Module Networks Be](https://arxiv.org/abs/2106.08170) pokazuje, że wynik zależy od stopnia i miejsca modularności; więcej modułów nie jest monotonicznie lepsze.

Decyzja: po sześciu testach świata następników priorytet przechodzi z kolejnego routingu/shardingu na HYP-0002 i wersjonowaną kohortę program-library transfer. Szczegóły: `research/reviews/GEN-0-REVIEW-2026-08-30.md`.
