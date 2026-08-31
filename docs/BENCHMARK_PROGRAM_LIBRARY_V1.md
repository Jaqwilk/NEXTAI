# `program_library_v1`

## Pytanie

Czy operator wydobyty bez etykiety z rozwiązanych programów zmniejsza koszt wyszukiwania na nowych kompozycjach, a nie tylko zapamiętuje identyczne zapytania?

## DSL i dane

- Cztery ręcznie dostarczone prymitywy są deterministycznymi permutacjami 31 stanów.
- K oznacza liczbę rozwiązanych programów treningowych; D oznacza długość programu testowego.
- Korpus zawiera powtarzający się fragment `(0, 1)` w różnych otoczeniach, ale nie przekazuje jego nazwy ani granic.
- Zadania testowe używają tego fragmentu w nowych układach i są opisane czterema parami wejście–wyjście; piąte wejście jest testem generalizacji.

## Porównania

| Kandydat | Rola |
|---|---|
| `random_program_guess` | kontrola ujemna |
| `primitive_program_search` | enumeracja wyłącznie z prymitywów |
| `exact_program_memo` | oddziela exact reuse od transferu biblioteki |
| `mismatched_library_search` | kontroluje narzut i przypadkową korzyść dodatkowego tokenu |
| `oracle_library_search` | górna granica ze znanym prawidłowym fragmentem |
| `learned_library_search` | wybiera fragment długości 2–3 przez prostą oszczędność MDL |

Wszystkie solvery znają D. Wyszukiwanie jest uporządkowane długością opisu w aktualnej bibliotece. `mean_query_ops` obejmuje rozwinięcia gramatyki i wykonania prymitywów. `fit_ops`, `state_bytes`, `update_ops` i `amortized_cold_ops` ujawniają koszt odkrycia oraz utrzymania biblioteki.

## Granice twierdzenia

To kontrolowany test search compression, nie języka, percepcji ani otwartego program synthesis. DSL jest ręczny, fragment jest wyjątkowo częsty, quick ma jeden seed, a długość rozwiązania jest znana. Wynik dodatni może jedynie uzasadnić trudniejszą replikację z mylącymi fragmentami, nie promocję architektury.
