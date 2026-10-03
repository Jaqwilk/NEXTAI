# Aktualny stan NEXTAI

Pakiet `AUDIT-REPAIR-20261002-V1` zakończył jedyny autoryzowany eksperyment
`EXP-20261002-0001` w oddzielnym klonie Git. Bieżąca decyzja to
`AUDIT-REPAIR-DECISION`; scoring jest wyłączony, rejestracja 1/1 zużyta.
Stan: 107 rezultatów, cykl 300, brak aktywnego i oczekującego EXP.
Zgoda i prospektywny kontrakt znajdują się w
`research/laboratory/AUDIT-REPAIR-20261002-V1.json` oraz
`research/plans/AUDIT-REPAIR-20261002-V1.json`.

Zweryfikowaną kolejkę i zużycie uprawnień wyznacza `uv run nextai lab status`.
Ten dokument jest opisem, nie dodatkową zgodą. Obowiązuje maintenance i brak
retry. Wszystkie 36 komórek kalibracji zakończyły się z integralnością PASS.
Accuracy: dense 23,6574%, uczony BM25 48,8426%, frozen BM25 15,1389%, symboliczny
graf 100%. Dense nie osiągnął zamrożonych progów 85% overall i 80% replacement.
Różnica uczony–frozen +33,7037 pp jest opisową obserwacją jednego seedu.

Stare etapy PC-01, WT-01, REVIEW-01 i MUC v1 pozostają zakończone. Nie zwiększamy
ich budżetów. Dane WT 8–9, harmonogram, zewnętrzne modele/API i mechanizm
delta-memory są poza zakresem. Zachowujemy wszystkie wyniki, porażki i źródła.

MUC v1 ma negatywną kontrolę uczoną i wadliwe koszty oraz etykiety pomiaru.
Nowa kohorta ma odrębną tożsamość; jej wyników nie łączymy z v1. Uczone role v2
to jawne czytniki par tekstowych z iteracyjną kompozycją, nie pełne autoregresyjne
LLM. Kalibracja nie ustanawia nowej architektury ani przewagi ekonomicznej.

Analiza: `research/analyses/EXP-20261002-0001.md`. Rozliczenie napraw:
`research/reviews/AUDIT-REPAIR-20261002-V1.md`. Pełna walidacja przed seedem:
1008/1008. Końcowa pełna regresja po dodatkowych poprawkach: 1013/1013,
zero błędów i skipów. Receipt: `research/laboratory/AUDIT-REPAIR-COMPLETION-V1.receipt.json`.

Dokładne źródła kalibracji z evaluatorem `ee6c5cb92dfdb95dcf79942352c0ca753ca0ffe79f458b225e8377ad5774d010`
zachowano w `research/laboratory/archive/AUDIT-REPAIR-CALIBRATION-20261002-V1`.
Po wyniku naprawiono brak fazy przy żywym heartbeat i wyścig krótkiego workera,
zgodnie z prospektywnym `AUDIT-REPAIR-SUPERVISOR-ADDENDUM-V1.json`.
Aktualny manifest `984ae108f07b2bf4f71dc7bc88faeff0b31c74dc5c39a1ad229461cd6cc777a2`
opisuje wyłącznie maintenance, nie wykonany wynik. Nowy scoring wymaga nowej
decyzji, prospektywnego kontraktu i świeżej kohorty. Najbliższa proponowana
kontrola dotyczy trudnych negatywów i fałszywych dopasowań matchera na nowych
train/dev; nie jest autoryzowanym eksperymentem.
