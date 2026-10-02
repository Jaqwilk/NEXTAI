# NEXTAI — laboratorium badawcze

Cel: szukać i rygorystycznie sprawdzać zasad obliczeniowych, które poprawiają
zdolność na jednostkę pełnego kosztu inferencji względem gęstych LLM.

Aktualny zakres: naprawy AUDIT-REPAIR-20261002-V1, walidacja na niezależnym
klonie Git i jeden prerejestrowany eksperyment kalibracyjny MUC v2.
Opis stanu: [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md).
Źródłem kolejki i zużycia zgód jest zweryfikowane `uv run nextai lab status`.

PC-01 potwierdził lokalną kontrolę uczenia. WT potwierdził wąski efekt
klasycznej rekurencji. MUC v1 nie przeszedł kalibracji uczonych kontroli;
wadliwe koszty i etykiety pozostają jawnie opisane w audycie. Nie ma
promowanej architektury, dowodu transferu ani przewagi nad LLM.

Historia, plany, wyniki i archiwa pozostają zachowane. Wersji benchmarków
nie łączymy. Nie ma klienta zewnętrznego modelu/API ani gwarancji przełomu.

## Sprawdzenie gotowości

```powershell
uv run nextai doctor
uv run nextai lab status
uv run pytest
```

Regresja ma obowiązkową ochronę WT 8–9. Testy fizycznych danych używają tylko
legalnych plików 0–7; testy legacy v3/v4 używają syntetycznych epizodów.
Doctor PASS potwierdza spójność, a nie uprawnienie do kolejnego eksperymentu.

Nowe środowisko wymaga kontroli miejsca: po instalacji i rozpakowaniu co
najmniej 10 GiB musi pozostać. Dopiero wtedy `uv sync --frozen --extra dev`.
Nie pobieramy danych ani modeli automatycznie. Używamy lokalnego środowiska
i audytowanego runnera `uv run nextai run --plan ...`.

## Zasady i historia

- AGENTS.md — niezmienne zasady rzetelności, uprawnienia i aktualna faza.
- program.md — jeden ograniczony cykl i konkretne warunki zatrzymania.
- docs/SCIENTIFIC_PROTOCOL.md — oddzielne testy mechanizmu, ekonomii i transferu.
- research/laboratory/restart.json — chroniona kolejka startowa.
- research/laboratory/BELIEFS_POLICY.md — opinie audytora nie są funkcją nagrody.
- research/plans, results, analyses, events.jsonl — nieusuwalna historia.
- research/REPORT.md + REPORT.provenance.json — raport z kontrolą treści wejść.
- docs/ORIGINAL_MANIFEST.md — zachowana pierwotna wizja.
- docs/ROADMAP.md — historyczna mapa G0–G8, nie aktualna kolejka.

Raport odświeża uv run nextai report. Nie naprawia się integralności przez
dotykanie dat plików ani zmianę starych wyników. Git ma jawne EOL z trzema
wyjątkami zachowującymi historyczne hashe. Zmiana chronionego harnessu wymaga
udokumentowanej migracji i nowego manifestu, nie automatycznej akceptacji.

## Zatrzymanie i ograniczenia

STOP lub PAUSE w katalogu głównym blokują kolejne cykle, plany i scoring.
Nie usuwać ich bez decyzji użytkownika. Aktywna blokada także zatrzymuje pracę.
Jeden cykl nie uruchamia drugiego eksperymentu ani zaległych serii catch-up.

Harmonogram aplikacji jest osobną konfiguracją. Zmiana dokumentacji go nie
uruchamia i nie potwierdza jego stanu. Tekst przyszłego wybudzenia znajduje
się w docs/AUTOMATION_PROMPT.md.

Widoczne lokalne dane są screeningiem, nie niezależnie ślepym holdoutem.
Audyt importów i osobny proces nie są pełnym sandboxem systemu operacyjnego.
Porównania GPU/CPU wymagają jawnych scenariuszy, jakości i pełnego kosztu.
Nie twierdzimy, że laboratorium ma już następcę LLM.
