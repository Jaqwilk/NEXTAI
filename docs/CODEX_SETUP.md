# Uruchomienie wyłącznie w Codexie

## Co faktycznie działa

Sterowanie badaniami wykonuje ten sam Codex w tym lokalnym zadaniu. Trwałość nie pochodzi z procesu modelowego działającego w tle, lecz z dwóch warstw:

1. repozytorium przechowuje stan, reguły, plany i wyniki;
2. harmonogram Codexa okresowo wraca do tej samej rozmowy i wykonuje jeden cykl.

Nie ma osobnego modelu, API, klucza ani demona. Komputer oraz aplikacja Codex muszą działać, aby lokalne zaplanowane wybudzenie mogło się wykonać. To celowa właściwość rozwiązania natywnego.

## Jednorazowa inicjalizacja

```powershell
uv sync --extra dev
uv run pytest
uv run nextai integrity verify
uv run nextai doctor
```

Manifest integralności jest tworzony dopiero po zatwierdzeniu wersji benchmarku. Protokół v2 haszuje cały harness, kandydatów, testy, schematy, lockfile i kontrakt naukowy; nadpisanie manifestu najpierw archiwizuje poprzednią treść. Zmiana chronionego pliku ma zatrzymać scoring, a nie zostać automatycznie zaakceptowana.

## Kontrakt zaplanowanego wybudzenia

Każde wybudzenie ma wykonać dokładnie jeden cykl:

1. przeczytać `AGENTS.md` i `program.md`;
2. sprawdzić STOP/PAUSE/lock/integrity;
3. dokończyć jedyny oczekujący plan, append-only go unieważnić albo wybrać jedno pytanie;
4. prerejestrować je przed implementacją;
5. uruchomić tylko lokalny, audytowany harness; dokładne scoring seeds ujawnia runner dopiero po audycie i zamrożeniu kodu;
6. zachować porażki i oddzielić obserwację od interpretacji;
7. zaktualizować raport, uruchomić testy i zakończyć do następnego wybudzenia.

Dokładny tekst automatyzacji jest zachowany w `docs/AUTOMATION_PROMPT.md`. Częstotliwość nie zmienia limitów eksperymentu; zapobiegają temu lock, jeden oczekujący plan i cadence gates.

## Ręczny cykl

Użytkownik może w dowolnym momencie napisać w tym zadaniu „kontynuuj”. Codex odczytuje trwały stan i podejmuje następny krok. Do diagnostyki bez rozpoczynania eksperymentu:

```powershell
uv run nextai doctor
uv run nextai hypothesis list
uv run nextai report
```

## Zatrzymanie

Utworzenie `STOP` lub `PAUSE` w katalogu głównym powoduje błąd `doctor`, `plan new` i `run`, więc blokada działa także wtedy, gdy prompt automatyzacji zostanie źle zinterpretowany. Harmonogram można również wstrzymać w aplikacji. Usunięcie pliku wznawia pracę tylko wtedy, gdy harmonogram nadal jest aktywny lub użytkownik poprosi Codexa o kontynuację.
