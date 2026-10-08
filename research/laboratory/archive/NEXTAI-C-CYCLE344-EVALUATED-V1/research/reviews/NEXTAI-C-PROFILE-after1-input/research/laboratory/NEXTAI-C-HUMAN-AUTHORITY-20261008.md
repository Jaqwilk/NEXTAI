Wznów główny cel NEXTAI. Na następne maksymalnie 12 godzin zatwierdzam osobny etap C: stabilizacja aktywnej ścieżki badań i jeden kompletny screen drugiej niezależnej rodziny.\
\
Przydzielam C oddzielny budżet do 43 200 s rozliczonej pracy oraz najwyżej jedną nową rejestrację naukową. Nie dodawaj tych środków do B. Zachowaj wszystkie wcześniejsze koszty, wykorzystane tickety, wyniki i niepowodzenia. Chronione sześć rejestracji i 41 000 s B pozostają nienaruszone.\
\
W C rozlicz również ujawnioną, dotąd nierozliczoną nadwyżkę administracyjną: co najmniej 110,724645 s. Ustal jej uzasadnioną wysokość z zachowanych dowodów; brak pomiaru oznacz jako niepewność, nie zero.\
\
Celem tego etapu jest:\
1\. Sprawna i zmierzona ścieżka walidacja → rejestracja → workery → analiza → zamknięcie.\
2\. Pełna techniczna wykonalność intake drugiej rodziny.\
3\. Jeden prerejestrowany screen: pięć sparowanych jednostek, trzy skale, mocne kontrole, pełne koszty, niepewność i decyzja.\
\
Pracuj autonomicznie. Jedna spójna prerejestracja etapu inżynierskiego ma obejmować zwykłe iteracje poprawek i testów. Zezwalam na poprawianie oraz ponawianie testów inżynierskich na publicznych lub syntetycznych fixtures w budżecie C. Nie wymagaj osobnej zgody po każdym błędzie takiego testu.\
\
Zakaz retry nadal obejmuje płatne próby naukowe. Nie ponawiaj zamkniętej replikacji HAR ani nie przywracaj zużytych danych jako świeżych.\
\
Orientacyjny podział czasu:\
\- do 3 godzin: rozliczenie, profilowanie i naprawy aktywnego harnessu;\
\- do 2 godzin: zamrożony intake i pełna conformance drugiej rodziny;\
\- do 4 godzin: jeden screen naukowy;\
\- do 1 godziny: analiza i raport;\
\- 2 godziny rezerwy na awarie i bezpieczne zamknięcie.\
To maksima, nie obowiązek wykorzystania całego czasu.\
\
Najpierw zamroź zakres napraw technicznych. Zmierz czas, pamięć i liczbę procesów poszczególnych bramek. Ustal rzeczywiste wąskie gardło. Nie ograniczaj naprawy do zwiększenia timeoutu.\
\
Dodaj walidację dry-run przyszłego planu, bez rejestracji naukowej i bez zużycia ticketu. Korzystaj z tego samego kodu budowy planu i tych samych bramek co rzeczywista rejestracja. Sprawdź pełny przebieg na izolowanych fixtures w klonie.\
\
Ogranicz powtarzane odczyty i walidacje tam, gdzie pomiar uzasadnia zmianę. Ewentualny cache musi być związany z hashami wejść i poprawnie unieważniany. Zachowaj kontrole integralności, przecieku, budżetów i kompletności wyników. Nie refaktoruj całej biblioteki historycznych kandydatów.\
\
Następnie oceń nową wersję zadania ASM. Nie zmieniaj zamkniętych planów. Przed implementacją nowego intake i dalszym odczytem danych zamroź kompletną regułę parsera, zakres współrzędnych, geometrię, kohortę, recepturę, metryki, progi, budżet i decyzję.\
\
Ujemne współrzędne można dopuścić wyłącznie jako jawnie uzasadnioną regułę nowej wersji zadania. Bez abs, clamp, usuwania punktów, pomijania próbek lub wybierania wygodnych writerów. Sprawdź zgodność dawnych zaakceptowanych tablic i widoków; zachowaj wszystkie wcześniejsze dowody.\
\
Używaj wyłącznie dozwolonej kohorty development T1–5/D16–20. Ujawnij wcześniejsze ekspozycje i nie nazywaj jej świeżym lub ślepym finałem. Przyszłe kohorty replikacji i finału pozostają zamknięte.\
\
Dopiero po pełnym intake, conformance, poprawnym dry-run, zamrożeniu źródeł, preflight i readiness wykonaj najwyżej jeden nowy screen, finansowany z C. Nie uruchamiaj próbnej płatnej rejestracji.\
\
Zachowaj istniejący model, 4096 par, recepturę 2048/1024 kroków, pięć sparowanych jednostek, K16/32/64, warunki nominal/adverse oraz naukowe metryki i progi. Bez ponownego treningu źródła i nowych architektur.\
\
Porównaj rzeczywiste zamrożone źródła z nieuczonymi i shuffled controls przy identycznej adaptacji, target transformerem oraz mocnymi metodami klasycznymi. Oddziel ranking, poprawne źródło, aktualizacje, zachowane fakty, UNKNOWN i błędną abstencję. Target-only fitting nie dowodzi transferu informacji ze źródła.\
\
Nie osłabiaj wymagań kompetencji, jakości, UNKNOWN, abstencji ani ekonomii. Jeśli transformer nie jest kompetentny, ekonomiczny wniosek pozostaje INCONCLUSIVE. Nie dostrajaj receptury po wynikach dev.\
\
Rozlicz pełne drzewa procesów, fit, kalibrację, preprocessing, ingest, indeksy, aktualizacje, kopie, cache, query, dekodowanie, testy i administrację. Nie sumuj ponownie zagnieżdżonych pomiarów. Limit pełnych workerów naukowych: 9000 s; łącznego supervised fitu: 3600 s. Oba mieszczą się w całym budżecie C.\
\
Na koniec zachowaj kod, konfigurację, surowe wyniki, hashe i dokładne polecenia odtworzenia. Dostarcz czytelny raport: wynik, przedziały niepewności, pełne koszty, decyzja i niewykonany zakres. Uaktualnij zwięzły aktualny status projektu, zachowując historię.\
\
Nie buduj w tym etapie prototypu ani nie deklaruj ukończenia całego głównego celu. Ten etap ma dostarczyć sprawne narzędzie i rzetelny wynik drugiej rodziny, potrzebne do dalszych replikacji, finałów i prototypu wybranego z dowodów.\
\
Bez WT8–9, zewnętrznych modeli/API i zmian harmonogramu. Przy awarii naukowej lub wyczerpaniu limitu zachowaj wynik i zamknij etap bez retry. Nie oznaczaj celu jako ukończonego na podstawie samych zielonych testów lub zużytego czasu.\
\
Etap A zachowuje dotychczasowy limit 17 rejestracji i 69 344 s, pomniejszony o całe zużycie. Po jego rozliczeniu zatwierdzam etap B: dodatkowe 12 rejestracji i 72 000 s. Rozliczaj fit, ewaluację, testy i nieudane wykonania; zarezerwuj środki na replikacje i świeży finał.\
\
Pracuj autonomicznie. Przed implementacją i nowymi danymi prerejestruj hipotezę, recepturę, metryki, progi, budżet i regułę decyzji. Waliduj w klonie. Rozdziel ranking, aktualizacje i UNKNOWN. Po porażce oceń alternatywy, nie tylko więcej kroków; nie osłabiaj kontroli ani kryteriów po wynikach.\
\
Dalszą drogę i prototyp wybierz z dowodów: mechanizm uczony, klasyczny lub hybrydowy. Zakończ odtwarzalnym porównaniem jakości i pełnych kosztów przy trzech skalach, niezależnych replikacjach i świeżym teście końcowym, z co najmniej pięcioma sparowanymi jednostkami danych/seedów. Raportuj niepewność i decyzję. Wynik negatywny jest dopuszczalny. Przy niewykonalności przedstaw dowody i alternatywy; przy wyczerpaniu limitów również niewykonany zakres. Sam limit nie oznacza ukończenia celu.