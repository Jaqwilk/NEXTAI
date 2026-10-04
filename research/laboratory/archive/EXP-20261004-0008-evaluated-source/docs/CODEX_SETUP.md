# Uruchomienie laboratorium w lokalnym zadaniu

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

Aktualny plan PC-01-FINAL-PREP-V1 przygotowuje kompatybilność serii v3.
Walidacja: `uv run python scripts/validate_pc01_final_preparation.py` po
ukończeniu i certyfikacji. Testy/manifest/certyfikat nie znoszą maintenance.
Po receipt potrzebna jest osobna decyzja o wykonaniu serii, bez kolejnego dev.

Sterowanie to bieżące zadanie Codexa i lokalny harness NEXTAI, bez dodatkowego
modelu/API. Aktualne instrukcje są w program.md i research/LAB_PLAN.md.
Trwały stan repozytorium ma pierwszeństwo przed historyczną kolejką w analizach.

Przygotowanie plików nie uruchamia automatyzacji. Jej rzeczywisty stan i prompt
należy sprawdzić w aplikacji przed wznowieniem; nie wnioskuj o nich z events.jsonl.
Tekst zgodny z protokołem v3 znajduje się w docs/AUTOMATION_PROMPT.md.
Aktualny krok odczytaj z lab status; nie powtarzaj ukończonego PC-01-CONTRACT.
Osobna zgoda PC-01-DEV2-20260905-V1 obejmuje tylko jedną nową próbę dev;
po jej wyniku wymagany jest przegląd, bez final i automatycznych ponowień.
Dev 2 ukończono; kolejny zatwierdzony PC-01-GPU-METADATA-V1 to wyłącznie
naprawa metadanych bez treningu. V3 pozostaje maintenance po jej walidacji.

## Kontrola lokalna

```powershell
uv run nextai doctor
uv run nextai lab status
uv run pytest
```

Przed instalacją uv sync --frozen --extra dev sprawdź wolne miejsce oraz
rozpakowany rozmiar i cache. Musi pozostać co najmniej 10 GiB. Nowy komputer
może wymagać lokalnych danych z manifestów; brak danych zgłasza się jawnie,
nie zastępuje ich innym zbiorem. Dużych danych nie dodajemy do Git.

Maintenance blokuje plan new i run, lecz nie blokuje dozwolonego przygotowania.
Manifest v3 obejmuje aktualny kontrakt i zachowuje archiwum v2. Samo freeze nie
uprawnia do scoringu. Nowa kohorta wymaga kontraktu, testów i certyfikatu.

STOP, PAUSE i aktywna blokada zatrzymują cykle. Jeden cykl kończy jeden krok;
brak nadrabiania równoległymi eksperymentami. Instrukcje nie gwarantują pracy
24/7. Lokalna praca zaplanowana wymaga włączonego komputera i aplikacji;
potwierdza to [oficjalna dokumentacja](https://learn.chatgpt.com/docs/automations?surface=app).
