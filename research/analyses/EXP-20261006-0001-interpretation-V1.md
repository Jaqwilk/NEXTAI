# MUC v2: interpretacja niezależnej replikacji

**Nie potwierdziliśmy, że ta receptura trudnych negatywów poprawia jednocześnie wybór faktów i rozpoznawanie braku odpowiedzi. Decyzja: DISCARD.** Eksperyment EXP-20261006-0001 ukończył pięć świeżych sparowanych seedów i wszystkie 11 ról. Model, 4096 par, 192 kroki oraz próg 0,5 pozostały niezmienione. Metryki i bramki zamrożono przed implementacją oraz danymi.

Ten dodatek wyjaśnia zapisany wynik; nie zmienia prerejestracji, pierwotnego raportu, jego hasza ani decyzji. Pełny raport to [EXP-20261006-0001.md](EXP-20261006-0001.md), a obliczenia zawiera `research/reviews/EXP-20261006-0001-paired-analysis.json`.

| Główna metryka | Losowe | Trudne | Różnica | CI 97,5% różnicy |
|---|---:|---:|---:|---:|
| Wybór najnowszego właściwego faktu przed odrzucaniem | 9,333% | 17,333% | +8,000 pp | [−3,869; +19,869] pp |
| Rozpoznawanie braku odpowiedzi nad wszystkimi rekordami | 30,000% | 15,852% | −14,148 pp | [−55,633; +27,336] pp |

Oba przedziały obejmują zero. Zaobserwowany dodatni sygnał rankingu nie jest potwierdzoną poprawą populacyjną według zamrożonej bramki. Spadek UNKNOWN jest obserwacją tej próby; szeroki przedział również nie daje pewnego dowodu pogorszenia w całym rozkładzie. Dwie główne metryki mają łącznie rodzinną pewność 95% dzięki korekcji Bonferroniego. Jednostką niepewności jest para seed/dane, nie pojedyncze pytanie.

| Para | Seed | Różnica rankingu | Różnica dense UNKNOWN |
|---|---:|---:|---:|
| 0 | 1676295826 | +3,333 pp | −34,815 pp |
| 1 | 1380025130 | +19,630 pp | +5,185 pp |
| 2 | 1444016924 | +2,222 pp | −50,000 pp |
| 3 | 197800381 | +11,852 pp | 0,000 pp |
| 4 | 815499825 | +2,963 pp | +8,889 pp |

Ranking poprawił się w 5/5 par, lecz UNKNOWN tylko w 2/5. Nie spełniono wymogu poprawy obu metryk, dodatnich dolnych granic CI i co najmniej 4 dodatnich par dla każdej z nich. Przekroczono też bramkę znanej abstencji: fałszywe odrzucanie znanych odpowiedzi wzrosło średnio z 0% do 9,481%, przy dopuszczalnym wzroście najwyżej 2 pp. Jego opisowy CI 95% to [−5,897; +24,860] pp.

Średnie bramki zaakceptowanych i końcowych znanych odpowiedzi przeszły, ale nie oznacza to bezpieczeństwa każdej pary. Para 0 miała 30% znanej abstencji; końcowa trafność znanych odpowiedzi spadła w niej z 27,513% do 15,079%, czyli o 12,434 pp. Te wyniki zachowano w analizie.

## Dlaczego wyniki UNKNOWN mają różne znaki

| Rodzaj braku odpowiedzi w diagnostyce dense | Losowe | Trudne |
|---|---:|---:|
| Brakujący podmiot | 0,000% | 8,148% |
| Brakująca relacja dla znanego podmiotu | 60,000% | 23,556% |

Spadek głównej średniej wiąże się przede wszystkim z gorszym wynikiem dla brakującej relacji. UNKNOWN w całym systemie wzrósł z 6,074% do 27,704% (+21,630 pp), ale to odrębna, opisowa metryka: inne pytania UNKNOWN oraz tylko czterej kandydaci po BM25 i mechanika ścieżek, zamiast maksimum nad wszystkimi rekordami. Jej CI 95% [−4,556; +47,815] pp obejmuje zero. Nie zastępuje ona wcześniej wybranej głównej metryki.

## Skala pamięci i granice wyniku

| K | Ranking: losowe → trudne | Dense UNKNOWN: losowe → trudne |
|---|---:|---:|
| 32 | 21,333% → 39,333% | 30,000% → 16,000% |
| 128 | 4,667% → 10,444% | 30,000% → 17,556% |
| 512 | 2,000% → 2,222% | 30,000% → 14,000% |

To opisowe podziały istniejących wyników. Korzyść rankingu jest większa przy małym K; nie wybieraliśmy korzystnego K po wynikach i nie zmienialiśmy wag dziewięciu komórek ani bramek. Niska bezwzględna trafność obu wariantów pozostaje istotnym ograniczeniem.

Wcześniejsza próba EXP-20261004-0001 również zakończyła się DISCARD. Miała średnie +12,148 pp rankingu i +13,407 pp dense UNKNOWN, z głównymi CI obejmującymi zero oraz przekroczeniem znanej abstencji. Nowa próba jest osobną replikacją: nie połączono wyników ani seedów i nie zastąpiono starej porażki. Kierunek efektu UNKNOWN nie powtórzył się. To wynik dotyczący konkretnego samplera, syntetycznej gramatyki, progu i budżetu treningu; nie falsyfikuje całej rodziny architektur lub treningu na trudnych negatywach.

## Koszty i weryfikacja

Nadzorowany fit wyniósł **115,413948/3600 s**. Wszyscy workerzy kosztowali **626,965224 s**, w tym kontrola symboliczna **3,949781 s** z zerowym fitem. Symboliczna kontrola uzyskała 100% trafności bez błędów parsera. Kontroler z rejestracją kosztował **1041,929174 s**; jego narzut wyniósł **414,963950 s**. Pełny czas etapu, łącznie z późniejszymi testami, dokumentacją i administracją, jest domknięty w osobnym końcowym rozliczeniu; pierwotny raport zachowuje pomiar do momentu jego utworzenia.

Zachowano wszystkie koszty generacji, przygotowania par, treningu, oceny, indeksowania, aktualizacji i diagnostyki. Dwa odrzucone zapisy konstrukcji odnoszą się do jednej unikalnej propozycji strukturalnej współdzielonej w parze; nie są retry fitu. Wszystkie 6077 zapisów i 2700 unikalnych zaakceptowanych światów zachowano w archiwum wykonania. Normalizowane przez Git kopie tekstowe nie zastępują archiwum surowych bajtów.

Przed treningiem przeszło 67 testów zgodności oraz Doctor i Lab w niezależnym klonie. Osobna kontrola wyników nie wykazała błędów świeżości, parowania, przeliczonych metryk, CI ani bramek. Końcowa reprodukcja i kontrole integralności są zapisane oddzielnie; nie wykonują nowych treningów lub eksperymentów. Energia i pieniądze nie były mierzone; nie wyciągamy wniosku o przewadze ekonomicznej.

W tym etapie zakres naukowy jest kompletny. Nie było retry, dostępu do WT 8–9, nowych architektur, zewnętrznych modeli/API ani zmiany harmonogramu. Historia i budżety wcześniejszych prób pozostają zachowane. Szerszy program B nadal jest aktywny, z niezmienioną rezerwą 7 rejestracji i 47000 sekund; ta replikacja nie kończy celu transferu i prototypu.
