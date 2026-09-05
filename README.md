# NEXTAI — laboratorium badawcze

## Aktualna zgoda — trzy repliki finalne

Obowiązuje research/laboratory/PC-01-FINAL-ACTIVATION-20260905-V1.json.
Użytkownik zatwierdził trzy świeże repliki niezmienionego modelu v3, po jednej
na cykl, 1200 s fit / 1800 s procesu każda, bez kolejnego dev, strojenia,
resume ani automatycznych powtórek. Najpierw freeze/certyfikat i rejestracja.
Awaria lub nieważny wynik zatrzymuje serię do przeglądu. Trzy kompletne wyniki
oceniamy razem według niezmienionych progów; bez awansu architektury.
Zatwierdzono także commity i nie-siłowy push do istniejącego GitHub origin;
duże dane i checkpointy zostają lokalnie. Nie zmieniamy harmonogramu.
Poniższe opisy zakończonych etapów pozostają historią, nie aktualnym zakazem.

Aktualny etap: `research/plans/PC-01-FINAL-PREP-V1.json` — przygotowanie
przejścia dev v2 → pomiar v3 i oceny trzech replik. Bez treningu i bez testu
finalnego. Po zakończeniu: PC-01-DECISION; uruchomienie wymaga osobnej zgody.
Stan i receipt mają pierwszeństwo przed opisami historycznych etapów poniżej.

Cel: szukać i rygorystycznie sprawdzać zasady obliczeniowe, które mogą poprawić
zdolność na jednostkę pełnego kosztu inferencji względem gęstych LLM.
Nie ma tu zewnętrznego modelu sterującego, klienta API ani gwarancji przełomu.

## Aktualny plan

Od 2026-09-04 obowiązuje LAB-RESTART-20260904-V1 i protokół v3.
Pełny plan: [research/LAB_PLAN.md](research/LAB_PLAN.md).

Kolejność: odtwarzalność i źródła -> pozytywna kontrola uczenia/pomiarów ->
wyjaśnienie wyniku WT -> przegląd decyzji -> dopiero warunkowo mały system
pamięci, aktualizacji i kompozycji z wejściem naturalnopodobnym.

Zachowano 99 historycznych wyników EXP i wszystkie porażki. Nowa faza
G2/infrastructure jest resetem strategii, nie dowodem zaliczenia dawnej G2.
Stara kohorta SuiteSparse nie jest aktywna; scoped gate blokuje jej scoring.
Archiwum pełnego protokołu v2 jest pod docs/archive/.

## Sprawdzenie gotowości

W istniejącym lokalnym środowisku:

```powershell
uv run nextai doctor
uv run nextai lab status
uv run nextai provenance --experiment EXP-20260831-0007 --candidate wt_candidate_under_test --revision 4952515
uv run pytest
```

Doctor PASS oznacza spójność infrastruktury. Lab status rozróżnia gotowość
przygotowania i gotowość scoringu. Aktualną kolejkę wyznaczają zweryfikowane
zgody i wyniki: PC-01-DEV2-20260905-V1 dopuszcza tylko jedną nową próbę dev
w kohorcie v2 po naprawie telemetrii, a po jej wyniku wymaga przeglądu.
Dev 2 zakończono. Aktualny PC-01-GPU-METADATA-V1 obejmuje tylko naprawę zapisu
metadanych GPU bez treningu; v3 pozostaje maintenance po walidacji.
Brak zgody na final lub automatyczny retry. Nie powtarzamy CAL-20260901-0001.

Nowe środowisko: najpierw sprawdź wolne miejsce i oszacuj środowisko, cache
oraz rozpakowane dane; minimum 10 GiB musi pozostać. Dopiero potem
uv sync --frozen --extra dev. Używamy uv.lock; nie pobieramy modeli ani danych
automatycznie. Konfiguracja Cloud Agent znajduje się w .cursor/ i stosuje tę
samą zasadę, a po instalacji uruchamia doctor. Bootstrap wymaga już dostępnego
Python 3.11+ i uv (lokalnie zweryfikowano 0.11.15); brak narzędzia zgłasza jako
blokadę, nie wykonuje nieprzypiętego instalatora sieciowego. Szacuje pełny zapas
dysku z uv.lock i trzyma cache oraz środowisko na sprawdzanym woluminie.

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
