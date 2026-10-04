# Prompt kolejnego cyklu laboratorium

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

Najnowszy zakres to PC-01-FINAL-PREP-V1, wyłącznie przygotowanie kontraktu
v2→v3 i syntetyczne testy serii. Po jego receipt lub terminie zakończ na
PC-01-DECISION. Żaden kolejny dev, freeze serii ani trening finalny nie jest
uprawniony. Nie włączaj harmonogramu i nie powtarzaj zakończonej naprawy GPU.

To tekst do użycia w istniejącym zadaniu po decyzji o kontynuacji. Ten plik
nie włącza harmonogramu i nie określa jego aktualnego stanu.

Kontynuuj NEXTAI w tym lokalnym repozytorium. Przeczytaj w całości AGENTS.md,
program.md, research/LAB_PLAN.md i research/laboratory/restart.json oraz wymagany
stan i ostatnie dowody. Uruchom uv run nextai doctor i uv run nextai lab status.
Wykonaj najwyżej jeden nazwany, ograniczony krok z aktualnego lab status.
Nie powtarzaj ukończonych etapów ani zużytych zgód; user_decision_required
oznacza stop. PC-01-DEV2-20260905-V1 pozwala jedynie na globalną próbę dev 2,
od inicjalizacji, 1200/1800 s, bez final i automatycznego retry; tę próbę zakończono.
Późniejszy PC-01-GPU-METADATA-V1 dopuszcza tylko ograniczoną naprawę metadanych,
bez treningu; v3 pozostaje maintenance po testach. Historyczne next_cycle,
SEARCH MODE i G1-POST-EXP-0059-V1 nie są aktualną kolejką. Nie uruchamiaj ponownie
CAL-20260901-0001, nie projektuj od razu zintegrowanej architektury.

STOP/PAUSE, aktywna blokada albo błędy integralności, schematów lub historii
zatrzymują cykl. Nie usuwaj blokady ani nie odświeżaj manifestu, aby ją obejść.
Nie uruchamiaj EXP w maintenance. Nowa kohorta wymaga zamrożonego kontraktu
właściwego dla uczenia, ekonomii lub transferu. Prerejestruj przed implementacją,
zachowaj wszystkie próby dev i porażki, użyj wyłącznie audytowanego runnera,
nie dobieraj progów/recipe po holdoucie. Respektuj limity etapów, dysku i procesu.
Nie uruchamiaj zewnętrznego modelu/API, nie publikuj i nie zmieniaj drugiego
laboratorium/worktree. Nie zwiększaj przekonań tylko po to, żeby wykazać postęp.

Na koniec zapisz artefakt, append-only zdarzenie z budżetem i kolejnym krokiem,
odśwież raport po treści, uruchom testy i doctor. Oddziel obserwacje,
interpretacje i niepewność. Nie zaczynaj drugiego eksperymentu ani catch-up.
Jeśli kolejny krok wymaga nowej zgody albo wyczerpano limit etapu, podaj dokładną
blokadę i zakończ. Bez zmiany istotnej dla użytkownika nie powtarzaj pustych
powiadomień o tym samym stanie.
