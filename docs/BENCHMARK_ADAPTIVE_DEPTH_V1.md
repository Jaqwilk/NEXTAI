# adaptive_depth_v1

Cel: sprawdzić HYP-0004 — czy obliczenia mogą rosnąć z ukrytą trudnością zapytania `D`, a nie z rozmiarem wejścia `K`.

Świat zawiera jedną ścieżkę długości `D`, zakończoną samopętlą, oraz nieistotne cykle. Kandydat dostaje graf i punkt startowy, ale nie dostaje `D`; sam decyduje, kiedy zakończyć. Odpowiedzią jest węzeł terminalny.

Kontrole:

- `random_guess`: kontrola negatywna;
- `fixed_short_indexed`: stały budżet 4, więc powinien zawodzić dla `D=16`;
- `fixed_max_indexed`: zawsze 16 kroków, poprawny, lecz nieadaptacyjny;
- `adaptive_linear_scan`: adaptacyjny, ale kosztowny względem `K`;
- `adaptive_indexed`: mechaniczny dodatni wzorzec `ops ~ D`, niezależny od `K`.

Benchmark nie dowodzi uczenia zatrzymania. Waliduje jedynie aparat i granicę kontrolną przed testem modelu uczącego się na `D<=4` i ocenianego poza rozkładem na `D=16`.
