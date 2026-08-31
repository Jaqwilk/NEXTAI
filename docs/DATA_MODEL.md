# Model danych i niezmienność historii

## Relacje

```text
hypothesis_events.jsonl (HYP, wiele rewizji)
             |
             +----< plans/EXP.json (jedna prerejestracja, SHA-256)
                            |
plan_registry.jsonl --------+
plan_status_events.jsonl ---+ (append-only invalidation)
                            |
                            +----1 results/EXP.json (surowe próby + agregaty)
                                      |
                                      +----1 analyses/EXP.md
                                      +----* experiments.tsv rows

eval_manifest.json ---- hashes ----> full harness / candidates / tests / protocol / lockfile
state.json ------------ mutable pointer, nie źródło wyniku
sources.jsonl --------- checked prior art
```

## Reguły zapisu

- Hipoteza jest event-sourced: aktualizacja tworzy wyższą `revision`, nigdy nie przepisuje starego wpisu.
- Plan jest prerejestracją. Jego kanoniczny JSON jest haszowany i zapisany w rejestrze. Po rejestracji nie wolno go poprawiać.
- Błędny plan pozostaje na dysku; `plan_status_events.jsonl` może wyłącznie dopisać jego unieważnienie wraz z powodem.
- Plan v2 przechowuje politykę/liczbę seedów. Wynik przechowuje dokładną macierz z seedami ujawnionymi przez runner po audycie kodu.
- Dla jednego ID eksperymentu istnieje najwyżej jeden plik wyniku. Ponowienie jest nowym eksperymentem z `parent_experiment_id`.
- `experiments.tsv` jest indeksem do szybkiego przeglądu, a nie źródłem prawdy; surowy wynik JSON ma pierwszeństwo.
- Analiza jest warstwą interpretacji. Nie wolno wkładać interpretacji do surowych obserwacji.
- `state.json` może wskazać aktywny cykl i ostatnie ukończone cadence review, ale nie może zmienić historycznego znaczenia planu ani wyniku.

## Schematy

| Dokument | Walidator | Rola |
|---|---|---|
| hipoteza | `schemas/hypothesis.schema.json` | teza, predykcje, falsyfikacja, prior, dowody i następny test |
| plan | `schemas/experiment_plan.schema.json` | niezmienna polityka eksperymentu przed wynikiem |
| wynik | `schemas/experiment_result.schema.json` | środowisko, integralność, trials, agregaty i Pareto |
| stan | `schemas/research_state.schema.json` | bieżąca generacja/cykl i blokada logiczna |
| źródło | `schemas/source.schema.json` | sprawdzone prior art i ograniczone twierdzenia |

## Rozszerzanie modelu

Zmiana pól wymaga podniesienia `schema_version` albo migracji jawnie opisanej w review. Nie wolno dodać pola tylko po to, aby uratować interpretację już zobaczonego wyniku. Nowa metryka trafia do nowej wersji benchmarku i wymaga ponownego uruchomienia baseline'ów.
