# GEN-1 — WT changepoints development baseline gate, cykl 117

Zakres: dokładnie jeden no-scoring development-only feasibility service na kontrakcie z cyklu
116. Nie utworzono benchmarku, evaluatora, hipotezy, planu, seeda scoringowego, kandydata ani
wyniku naukowego. Testowe pliki seed 8–9 nie zostały odczytane.

## Prerejestracja przed development outcomes

Skrypt `research/audits/wt_changepoints_dev_baseline_preflight_v1.py` najpierw użył wyłącznie
train seedów 0–5. Zamroził artefakt
`research/checks/wt_changepoints_dev_baseline_gate_preregistered_v1.json` o SHA-256
`1897d63d790b575a892b04a7eb45c99927d7a46eeebd4c0399bd9740b69e60ff`. Hash skryptu
`8a1ea01ff897b82679c501a418b798998547b04304c8ee13bf833466548ffd33` był następnie
sprawdzany przed evaluacją.

Train-only niezależny bootstrap persistence (2048 powtórzeń) zamroził p95 różnicy NRMSE
`0.111215` / `0.115637` / `0.132527` dla H16/H32/H96. Minimum meaningful effect ustalono
z góry na maksimum, `0.1325268421`. Baseline uznano by za trywialne rozwiązanie tylko przy
pełnej finitości, H96 NRMSE <= `0.50` oraz worst-file H96 <= `0.75`.

Zamrożone kontrolki to: persistence, średnia residual curve grupowana dokładnym publicznym
poziomem sterowania oraz source-identical pooled linear initialization z ridge `0.001` i
forgetting `1`, aktualizowana RLS wyłącznie w lokalnym stanie pliku po reveal. Normalizacja,
32-elementowy anonimowy feature contract, fit depth 32 i horyzonty 16/32/96 pochodzą wyłącznie
z train.

## Obserwacje development

| baseline | H16 NRMSE | H32 NRMSE | H96 NRMSE | worst-file H96 | finite |
|---|---:|---:|---:|---:|---:|
| persistence | 0.973928 | 1.028452 | 1.096524 | 1.167073 | 1.0 |
| exact control-level bank | 0.943017 | 0.951047 | 0.989094 | 1.055685 | 1.0 |
| slot-local RLS | 0.855294 | 0.870563 | 0.876661 | 0.926106 | 1.0 |

Control-level bank poprawił persistence o `0.030911`, `0.077405`, `0.107430`; żadna różnica
nie przekroczyła zamrożonego efektu. RLS poprawił go o `0.118633`, `0.157889`, `0.219863`;
H32 i H96 przekroczyły próg, H16 nie. Żaden baseline nie spełnił kryterium saturacji.

Odczytano osiem plików train/development, łącznie `4,593,906` B. Szacowany state exact-level
bank to `30,720` B; slot-local RLS `253,952` B na plik. Szacowane query work na epizod wynosi
odpowiednio `960`, `960` i `61,440` operacji. Te jawne szacunki są diagnostyką feasibility,
nie pełnym kosztem przyszłego benchmarku.

Pierwsza próba po obliczeniu development zakończyła się przed zapisem artefaktu na błędzie
serializacji względnej ścieżki: `Path.relative_to` otrzymał względny argument i absolutny root.
Nie zmieniono kodu, modelu, progu ani prerejestracji. Ten sam skrypt i te same hashe uruchomiono
ponownie z absolutną ścieżką prerejestracji; powstał artefakt
`research/checks/wt_changepoints_dev_baseline_preflight_v1.json` o SHA-256
`65ac40a66d156f421ded4dd80b77d0147cd9f7f276d174e1f662001a43993424`.

## Interpretacja i niepewność

Jawny control-level router nie niesie gotowego rozwiązania. Prosty adaptacyjny model liniowy
wydobywa realny sygnał na dłuższych horyzontach, lecz jego błąd pozostaje duży i nie saturuje
zadania. Dane zatem przechodzą najtańszą bramkę nietrywialności oraz mają miejsce na test
lepszego lokalnego mechanizmu.

To nie dowodzi, że przyszły learner może wygrać. Preflight nie uruchamiał jeszcze pełnego
change-point banku, bounded replay ani ridge/FIR wymaganych przez prospective contract. Te
kontrolki muszą być zaimplementowane i semantycznie sprawdzone w osobnym chronionym cyklu,
a ich development smoke nadal może odrzucić benchmark przed aktywacją.

Confidence `0.995` dla liczb i braku saturacji według zamrożonego kryterium. Confidence `0.85`,
że zadanie jest nietrywialne dla testowanych prostych kontrolek; niepewność wynika z dwóch
plików development, lokalnej widoczności danych i brakujących jeszcze silniejszych kontrolek.

## Decyzja

`pass_for_later_protected_benchmark_service`. Nie tworzyć jeszcze hipotezy, planu ani scoringu.
Artefakt jest diagnostyką infrastrukturalną i nie może zmieniać evidence/confidence hipotez.

## Następny rozstrzygający krok

Dokładnie jeden protected service-only cycle dla nowej, oddzielnej kohorty
`heldout_wt_changepoints_prequential_v1`. Ma zaimplementować zamrożony split, anonimowy
predict–atomic-artifact–reveal–slot-update boundary, H16/32/96, K18/36/54, pełne koszty oraz
wszystkie obowiązkowe kontrolki i fixture leakage/permutation/local-update. Musi uruchomić ich
development-only smoke bez seedów 8–9 i odrzucić aktywację, jeśli dowolna silniejsza kontrolka
saturuje zamrożone `0.50/0.75`. Dopiero pełne semantic tests, preflight certificate, pytest,
integrity i doctor PASS mogą zamrozić nowy manifest. W tym następnym cyklu nadal nie wolno
tworzyć hipotezy, planu, seeda ani scoringu.
