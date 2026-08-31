# GEN-1 — primary-source intervention dataset gate, cykl 114

Zakres: jeden no-scoring source gate po wyniku
`no_identifiable_natural_intervention_contract` z cyklu 113. Porównano najwyżej trzy
rzeczywiste źródła: Causal Chambers `wt_changepoints_v1`, SKAB v0.9 i SWaT A1.
Sprawdzono wyłącznie publikacje autorów, oficjalne repozytoria, protokoły generatorów,
warunki dostępu i metadane HTTP. Nie pobrano zbioru, nie utworzono benchmarku, schematu,
hipotezy, planu eksperymentu, seeda, kandydata ani wyniku i nie wykonano scoringu.

## Zamrożona bramka

Źródło można wybrać tylko wtedy, gdy oficjalne materiały potwierdzają łącznie:

1. realny system fizyczny i powtarzane interwencje wewnątrz trajektorii;
2. obserwowalne pre/post outcomes i konstrukcję predict-then-reveal;
3. co najmniej trzy prerejestrowalne skale;
4. publiczne sterowania możliwe do anonimizacji bez ręcznej ontologii niosącej rozwiązanie;
5. stabilną licencję, proweniencję, bezpośredni bounded download i kontrolę integralności.

## Obserwacje źródłowe

| Źródło | Obserwacje | Wynik |
|---|---|---|
| Causal Chambers `wt_changepoints_v1` | Fizyczny wind tunnel. Oficjalny opis mówi o wielokrotnych losowych zmianach poziomu jednego aktuatora i losowej liczbie pomiarów po każdej zmianie. Generator tworzy 10 niezależnych sekwencji, każdą z 10 interwencjami, czterema poziomami `{0.01, 0.1, 0.2, 0.5}` i 100–300 pomiarami na odcinek. Pierwszy pomiar po zmianie ma `intervention=1`. Dane są CC BY 4.0; bezpośredni ZIP ma oficjalny MD5 `7e9f26d192674f2aaa6481f4415007eb`; HEAD zwrócił HTTP 200, 739333 B, ETag zgodny z MD5 i Last-Modified 2024-04-15. | **PROVISIONAL PASS** — jedyne źródło dopuszczone do osobnego acquisition/provenance gate. |
| SKAB v0.9 | Rzeczywisty water-circulation testbed, 35 CSV i wiele typów awarii. Oficjalny README stwierdza jednak, że każdy plik jest osobnym eksperymentem i zawiera pojedynczą anomalię. Powtórzenie wymagałoby łączenia plików katalogami `valve1`, `valve2`, `other`, czyli semantyczną etykietą typu awarii. | **FAIL** — brak powtarzanych interwencji wewnątrz trajektorii i family-blind recurrence. |
| SWaT A1 | Rzeczywisty sześciostopniowy water-treatment testbed, 11 dni ciągłej pracy, 51 sensorów/aktuatorów i 41 ataków w czterech dniach. Dostęp wymaga ręcznego wniosku; warunki zabraniają udostępniania danych nawet prywatnie i wymagają osobnego wniosku dla każdego odbiorcy. Oficjalna strona nie podaje bounded rozmiaru A1 ani publicznego checksumu. | **FAIL** — brak bezpośredniej, reprodukowalnej akwizycji i freezeable public provenance w tym repozytorium. |

## Dlaczego PASS jest tylko warunkowy

`wt_changepoints_v1` dostarcza dokładnie brakującą strukturę obserwacyjną, lecz opis strony
nie dowodzi jeszcze zawartości każdego CSV. Przed jakimkolwiek projektem benchmarku trzeba
lokalnie sprawdzić hash archiwum, bezpiecznie rozpakować je do wydzielonego katalogu, policzyć
rzeczywiste wiersze/segmenty/poziomy w każdym z 10 eksperymentów i potwierdzić, że znacznik
interwencji nie ujawnia targetu. Cztery poziomy są potencjalnymi skalami perturbacji; nie wolno
jeszcze utożsamiać ich z K ani wybrać targetu/metryki przed audytem danych.

Mechaniczna anonimizacja może usunąć nazwy kanałów i permutować kolumny, pozostawiając jeden
numeryczny control channel oraz anonymous outcome vector. To nie dostarcza learnerowi mapy
przyczynowej ani typu systemu. Czy taki lossless boundary jest rzeczywiście możliwy, pozostaje
pytaniem dla późniejszego service-design gate, a nie założeniem tego cyklu.

## Interpretacja i niepewność

Causal Chambers usuwa konkretną blokadę danych wykrytą w cyklu 113: w pojedynczej realnej
trajektorii istnieją wielokrotne, kontrolowane, nawracające zmiany z długimi odpowiedziami
post-intervention. Nie jest to evidence dla jakiegokolwiek learnera ani powód do promotion.
Źródło jest małym fizycznym sanity checkiem, a nie substytutem złożonego świata.

Confidence `0.98`, że `wt_changepoints_v1` jako jedyne z trzech przechodzi bramkę źródłową.
Niepewność dotyczy rzeczywistej kompletności/układu CSV, częstości każdego z czterech poziomów,
bezpiecznej anonimizacji i możliwości zdefiniowania mocnego prequential task bez target leakage.

## Decyzja

`select_wt_changepoints_v1_for_acquisition_gate_only`. Nie wybierać SKAB ani SWaT dla tego
kontraktu. Nie tworzyć jeszcze HYP-0028, EXP-20260831-0006, benchmarku lub evaluatora.

## Następny rozstrzygający krok

Następny wake może wykonać dokładnie jeden no-scoring **local acquisition/provenance service
cycle** dla `wt_changepoints_v1`:

1. pobrać wyłącznie oficjalny ZIP 739333 B do lokalnego, gitignored katalogu;
2. sprawdzić MD5 `7e9f26d192674f2aaa6481f4415007eb`, policzyć SHA-256 i zapisać URL/rozmiar/digest;
3. przed ekstrakcją odrzucić absolute paths, `..`, linki i wyjścia poza katalog docelowy;
4. zinwentaryzować dokładnie pliki, wiersze, kolumny, nie-finite values, intervention markers,
   długości segmentów, cztery poziomy i recurrence na każdy seed;
5. sprawdzić prospective predict-then-reveal oraz target-leakage boundary wyłącznie opisowo;
6. zapisać minimalny immutable local data manifest i audit report.

Brak checksum match, 10 poprawnych sekwencji, powtarzalnych interwencji, co najmniej trzech
poziomów albo anonimowego prequential boundary kończy kierunek jako
`acquisition_or_contract_failed`. PASS zezwala dopiero w kolejnym wake na service-design gate;
nie zezwala na hipotezę, plan, seed ani scoring.
