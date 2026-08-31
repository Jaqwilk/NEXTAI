# NEXTAI Autoresearch

To jest natywne dla Codexa środowisko do długotrwałych, falsyfikowalnych badań nad architekturami obliczeniowymi mogącymi kiedyś stanowić alternatywę dla dzisiejszych LLM-ów.

Nie ma tu klienta OpenAI API, klucza API ani osobnego modelu sterującego. Codex jest naukowcem: czyta `AGENTS.md` i `program.md`, tworzy prerejestrację, implementuje jeden ograniczony eksperyment, uruchamia lokalny harness i aktualizuje ledger. Harmonogram Codexa może okresowo wracać do tej samej rozmowy i wykonać kolejny cykl.

## Co już jest rozstrzygnięte

Manifest jest sensowny jako **program badań nad prawami skalowania**, lecz nie jako dowód, że ACC/SCCS albo jakakolwiek konkretna architektura zadziała. Repozytorium wymusza więc:

- wiele małych, różnorodnych zakładów;
- prerejestrację przewidywań i kryteriów porażki;
- niezmienność harnessu ewaluacyjnego;
- porównania przy dopasowanych budżetach;
- rozdzielenie obserwacji od interpretacji;
- replikację niespodziewanych wyników;
- pełny koszt końca-do-końca bez ukrywania pracy w LLM-ie, retrieverze lub przygotowaniu danych;
- osobny front Pareto dla implementowalnych kandydatów oraz oracle jako lower bounds;
- trwałe zachowanie nieudanych eksperymentów.

Pełna ocena znajduje się w `docs/OCENA_POMYSLU.md`, a kanoniczny protokół w `docs/SCIENTIFIC_PROTOCOL.md`.

Dokumentacja projektu obejmuje również:

- `docs/ORIGINAL_MANIFEST.md` — zachowany tekst źródłowy (znormalizowane zakończenia linii);
- `docs/PRIOR_ART.md` — najbliżsi poprzednicy i test granicy nowości;
- `docs/IDEA_CATALOG.md` — pełny katalog rodzin i tanich testów zabijających;
- `docs/ROADMAP.md` — generacje G0–G8 z bramami dowodowymi;
- `docs/METRICS.md` i `docs/DATA_MODEL.md` — rachunek kosztów, Pareto i schemat historii;
- `docs/SAFETY.md` — granice autonomii, zasobów i zaufania;
- `docs/CODEX_SETUP.md` — działanie wyłącznie w Codexie i zasady wybudzeń.

## Szybki start

W PowerShell:

```powershell
uv sync --extra dev
uv run nextai doctor
uv run pytest
uv run nextai report
```

Pierwszy kontrolny eksperyment:

```powershell
uv run nextai plan new `
  --hypothesis HYP-0001 `
  --title "Generation-0 baseline" `
  --question "Czy harness odzyskuje znane różnice skalowania K i D?" `
  --family "infrastructure_control" `
  --candidates random_guess linear_scan indexed_graph memoized_graph compiled_jump dense_recurrent `
  --budget quick `
  --prediction "Kontrole odzyskają jakościowo odmienne prawa kosztu." `
  --kill-criterion "Harness nie rozdziela znanych praw skalowania." `
  --promotion-criterion "Wszystkie kontrole zachowują się zgodnie z mechanizmem." `
  --alternative "Instrumentacja, a nie mechanizm, tworzy obserwowane różnice." `
  --confound "Mikrobenchmark jest zbyt mały dla stabilnego pomiaru czasu." `
  --positive-conclusion "Infrastruktura nadaje się do kolejnego testu G0." `
  --null-conclusion "Należy poprawić instrumentację bez wnioskowania o rodzinach." `
  --negative-conclusion "Harness nie nadaje się jeszcze do badań architektury."
uv run nextai run --plan research/plans/<utworzony-plik>.json
uv run nextai report
```

Polecenie `plan new` wypisuje dokładną ścieżkę. Plan jest niezmienny od chwili rejestracji; błędny plan zachowuje się i unieważnia poleceniem `nextai plan invalidate`. Nowy plan zapisuje politykę i liczbę seedów, natomiast ich wartości runner losuje dopiero po zamrożeniu i audycie kodu, a następnie utrwala w wyniku.

## Jak działa jeden cykl Codexa

1. Sprawdza `STOP`, `PAUSE`, blokadę i integralność harnessu.
2. Czyta stan, ledger, hipotezy i ostatnie wyniki.
3. Wybiera pytanie o największej oczekiwanej wartości informacyjnej.
4. Zapisuje plan **przed** implementacją i uruchomieniem; tylko jeden plan może oczekiwać.
5. Implementuje lub wybiera kandydata w dozwolonym zakresie.
6. Uruchamia `quick` na niewidocznych wcześniej seedach; dopiero wynik zasługujący na replikację dostaje `screen`.
7. Zapisuje obserwację, interpretację, pewność i następny test rozróżniający.
8. Aktualizuje hipotezę oraz raport; nie usuwa porażek.

Szczegółowy kontrakt znajduje się w `program.md`.

## Bezpieczne zatrzymanie

- Utwórz plik `STOP`, aby kolejne cykle nie rozpoczynały pracy.
- Utwórz `PAUSE`, aby wstrzymać nowe eksperymenty bez zamykania projektu.
- Usuń odpowiedni plik dopiero wtedy, gdy chcesz wznowić pracę.
- `doctor`, `plan new` i `run` traktują te pliki jako błędy blokujące, a nie informacyjne ostrzeżenia.
- Aktywne zadanie cykliczne można niezależnie wstrzymać w widoku Scheduled w aplikacji.

## Stan protokołu v2

- G0 zakończyło się po 35 wynikach jako szeroki screening metodologiczny; nie odkryto jeszcze promowanego następcy ani niedominowanej przewagi learned end-to-end.
- Projekt jest w G1/consolidation. Ostatni benchmark jest oznaczony `retired`, a EXP-0036 unieważniony bez scoringu. Nowy cykl musi najpierw przygotować czystą kohortę v2 i zamrozić jej manifest.
- `STOP/PAUSE`, kompletność plan→wynik→analiza→raport, kadencje review oraz promocje są egzekwowane przez kod.

## Ograniczenia wersji 0.2

- Harness uruchamia kandydatów w osobnym procesie, usuwa sekrety ze środowiska, kontroluje czas/RSS i audytuje importy. To ogranicza błędy, ale **nie jest granicą bezpieczeństwa systemu operacyjnego**.
- Pierwszy mikroworld bada pamięć, lokalne wnioskowanie, głębokość, aktualizacje i koszt. Nie mierzy jeszcze języka ani inteligencji ogólnej.
- Prawdziwie ślepy holdout wymaga izolowanego ewaluatora, którego Codex nie może odczytać. Wynik lokalny jest screeningiem, nie podstawą do twierdzeń o przełomie.
- Obecny harness jest CPU-first; osobna, jawnie wersjonowana konfiguracja GPU będzie potrzebna przed porównaniami z nowoczesnym Transformerem, Mambą lub BLT.

## Najważniejsze katalogi

```text
AGENTS.md                 stałe instrukcje ładowane przez Codexa
program.md                dokładny protokół pojedynczego cyklu
config/                   budżety i niezmienne definicje metryk
docs/                     ocena, doktryna, metodologia i roadmapa
schemas/                  kontrakty danych JSON Schema
src/nextai_autoresearch/  lokalny harness bez modelu/API
research/                 stan, hipotezy, plany, wyniki i ledger
tests/                    testy integralności i zachowania
```
