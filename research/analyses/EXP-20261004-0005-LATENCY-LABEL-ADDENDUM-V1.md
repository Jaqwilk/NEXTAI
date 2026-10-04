# EXP-20261004-0005 — doprecyzowanie etykiety p95

W oryginalnej analizie określenie „średnia p95 komórek” było błędne. Liczby tabeli pozostają poprawne: dla każdego workera `aggregate_trials` obliczało p95 z wszystkich 2880 surowych czasów zapytań, następnie tabela uśredniała te pięć percentyli po niezależnych jednostkach. Potwierdzono zgodność zapisanej statystyki z surowymi próbkami dla wszystkich 40 workerów i z zachowanym kodem źródłowym.

Nie zmieniono planu, wyniku, liczb, decyzji ani budżetu EXP-20261004-0005. Oryginalna analiza pozostaje niezmienna. Jest to dopisek do opisu, bez fitu lub ponownej ewaluacji. Szczegóły: `research/reviews/PVM01-DELTA-diagnostic-label-conformance-and-plot-V2.json`.
