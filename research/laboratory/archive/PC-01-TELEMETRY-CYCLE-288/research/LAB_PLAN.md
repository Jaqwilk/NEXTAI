# Plan uruchomienia laboratorium NEXTAI

Identyfikator: LAB-RESTART-20260904-V1. Data: 2026-09-04.
Status: próba dev zachowana jako inconclusive; zatwierdzona naprawa telemetrii bez treningu.
Cel programu nie zmienia się: lepsza zdolność na jednostkę pełnego kosztu
inferencji niż gęste autoregresyjne LLM. Żadna architektura nie jest z góry wybrana.

## 1. Decyzja po audycie i dodatkowej walidacji

Nie odrzucamy dotychczasowej historii. Odrzucamy utożsamienie braku spełnienia
bardzo silnej koniunkcji G1 z brakiem jakiegokolwiek użytecznego efektu uczenia.
Najpierw sprawdzamy aparaturę, potem wąskie efekty, ekonomię, a dopiero potem
transfer. Nie zaczynamy od dużego zintegrowanego systemu.

Ten plan jest aktualną kolejką i zastępuje stare sugestie next_cycle/SEARCH MODE,
ale ich nie usuwa. Licznik historii pozostaje ciągły. G2/infrastructure oznacza
reset strategiczny, nie zaliczenie dawnych bram zdolności G2.

## 2. Co rzeczywiście wynika z ponownej kontroli

Źródłem jest research/reviews/EXTERNAL-AUDIT-2026-09-03.md, draft
research/BELIEFS.json oraz niezmienne wyniki i kod. Audyt traktujemy poważnie,
ale poniższe ograniczenia są równie ważne jak jego trafne zarzuty.

| Ustalenie | Znaczenie dla planu |
|---|---|
| 99 wyników EXP, 88 jednoseedowych i 11 trzyseedowych; 4 wyniki mają append-only invalidację | Zachować pełną historię; nie zamieniać screeningu w replikację |
| Zidentyfikowano 3 chronione pliki, których historyczne hashe dotyczą CRLF, oraz kontrolę świeżości raportu zależną od dat plików | Ustalić zakończenia linii i kontrolować treść raportu |
| Później zmieniono plik wt_candidate_under_test.py; nie jest to kod wyników WT 0006/0007 | Przed interpretacją rozwiązać źródło po hashu z wyniku |
| WT ma wąski dodatni wynik jakości, ale nie ustaloną przyczynę ani przewagę pełnego kosztu | Osobny, zamrożony test rekurencji, RLS i ograniczenia amplitudy |
| 3 permutacje tych samych 2 śladów WT nie są 3 niezależnymi zbiorami fizycznymi | Nowe niezależne ślady dla replikacji; permutacje raportować oddzielnie |
| Kontrola pushdown uogólnia zamykanie nawiasów, lecz stos push/pop jest napisany ręcznie | Zachować wąski wynik; nie twierdzić, że odkryto ogólny operator |
| CAL-20260901-0001 porównywała różną jakość i różne tryby batchowania | To diagnostyka, nie ranking architektur przy tej samej jakości |
| Są ścieżki GPU i uczenie gradientowe także poza bezpośrednim importem torch | Nie powtarzać tezy „zero GPU/zero neural”; zapisywać faktyczne urządzenie i trening |
| Brak porządnie ustalonej kontroli małego transformera na właściwym zadaniu | Najpierw kompetentny pozytywny test uczenia, nie arbitralnie krótki trening |
| Zmiana pewności BELIEFS o 0.05 byłaby celem podatnym na manipulację | Mierzyć rozstrzygnięte pytania i nowe dowody, nie wielkość zmiany opinii |

Dokładny WT dla EXP-20260831-0006/0007: commit 4952515, źródło
src/nextai_autoresearch/candidates/wt_candidate_under_test.py, SHA-256
4471f2a999f9432e9d2e6fb56d309ebe7af52cca6dff246ab1b439b38f035104.
Wiążący hash odczytujemy poleceniem provenance z niezmiennego wyniku.

Model historyczny to ridge na [1, current, delta, control], rekurencyjne
przewidywanie, ograniczenie do +/-4 względem początku i lokalna aktualizacja RLS.
Algebraicznie jest to afiniczny VAR(2) z wejściem i clippingiem. To ważna
alternatywa, nie samo w sobie unieważnienie efektu. Wynik 0006: NRMSE około
0.6728 vs 1.0071; R16 około 16.683M vs 7.887M. Lepsza jakość przy wyższym
koszcie nie jest dominacją ekonomiczną. Źródła: wyniki 0006/0007 i ich audit.

CAL-20260901-0001 pozostaje nietykalna: PPM 2.1678 bpb / 1.7175 s;
tiny transformer 4.6247 bpb / 0.4803 s, trening około 0.6801 s.
GPU mierzył batche z prawdziwym kontekstem, a nie pojedynczą autoregresyjną
generację. Nie zmierzono energii. Nie powtarzamy tej kalibracji.

Dla kosztów przeliczona korelacja rang operacje–czas zapytania w 805 ważnych
wierszach wynosi około 0.806; w 571 z zamrożonym kontraktem Pareto około 0.671.
To opis historycznych zapytań, nie dowód uniwersalnej miary kosztu end-to-end.
W EXP-20260901-0036 R oznacza cały workload; wyliczone przecięcie około R=55.3
nie oznacza 55 pojedynczych pytań i nie usuwa różnicy pamięci.
Zapis zdarzenia o usunięciu cooldownu nie dowodzi zmiany częstotliwości heartbeatu.
Nie wnioskujemy o aktualnym stanie harmonogramu z dawnych analiz.

## 3. Etap R0 — odtwarzalność i pochodzenie

Dostarczamy w przygotowaniu:

- jawną politykę Git EOL z zachowaniem 3 historycznych hashy;
- świeżość raportu po treści wejść i renderera, odporną na kopiowanie/touch;
- narzędzie provenance: wynik -> zapisane zależności -> dokładne bajty z Git;
- kopię starego protokołu i archiwum manifestu; nową tożsamość protokołu v3;
- testy pozytywne i negatywne powyższych kontroli;
- kontrolę kopii checkoutu z ustawieniami LF i CRLF bez przepisywania danych;
- jawne rozróżnienie testu checkoutu na Windows od faktycznego testu Linux.

Nie zmieniamy wyników, planów, ledgerów hipotez, kandydatów ani benchmarków.
Stara kohorta SuiteSparse pozostaje dostępna historycznie, ale ma maintenance.
Brak nowych źródeł danych i modeli pobranych w tej fazie.

## 4. Etap PC-01 — pozytywna kontrola uczenia i pomiarów

Pierwszy następny cykl: przygotować kontrakt PC-01, bez treningu i scoringu.
Najpierw wybrać konkretną publiczną licencjonowaną lokalną próbkę danych i
kompetentną opublikowaną receptę małego transformera. Ustalić rozmiar modelu,
tokenizację, długość kontekstu, optymalizator, kroki, learning curve, early stopping
tylko na dev, limity czasu/RAM/VRAM i selekcję przed finalnym wynikiem.
Nie wybierać zbioru dlatego, że już wiadomo, kto na nim wygrywa w tym repo.

Obowiązkowe rozdzielone pytania:

1. Czy kontrola rzeczywiście uczy się w sensownym budżecie i poprawia jakość
   wobec tej samej nieuczonej/zamrożonej wersji?
2. Czy liczenie jakości wykrywa celowo błędne targety/wyłączone uczenie,
   przeciek oraz znane odpowiedzi kontrolne?
3. Czy pomiar odzyskuje osobno batch=1 latency i throughput dla zadanych batchy,
   z synchronizacją GPU, powtórzeniami, rozgrzewką oraz kosztami wejścia/wyjścia?

Nie wymagamy zwycięstwa transformera nad PPM/CTW na dowolnie małych danych.
Nie wymagamy lokalnego update ani cross-family do potwierdzenia uczenia.
Dla pytania ekonomicznego dodajemy mocne klasyczne baseline'y i dopasowanie
jakości; porażka takiego porównania nie kasuje dodatniej kontroli uczenia.

Przed aktywacją: nowy evaluator/cohort, osobny audytowany kontrakt, testy kontroli,
źródła pierwotne, licencja i hashe danych, jednostka podziału, progi efektu oraz
surowe pomiary. Nie wykorzystujemy do tego starego identyfikatora CAL.
Nowa kalibracja pozostaje diagnostyką, bez promocji architektury.

Limit: najwyżej 2 cykle projektowania/serwisu (łącznie 120 minut pracy narzędzi),
następnie najwyżej 3 prerejestrowane próby dev i 120 minut łącznego treningu
na lokalnym urządzeniu. Twardy limit każdej próby, procesów i pamięci musi być
niższy lub równy dostępnemu budżetowi i zamrożony w kontrakcie; nie zwiększamy
go po zobaczeniu wyniku. Replikacja kontroli: minimum 3 seedy, osobny zamrożony
budżet przed finalnym testem. To pułap programu, nie zgoda na obejście limitów
runnera. Jeśli nie wystarcza, raport dokładnej blokady i decyzja użytkownika.

Dodatek autoryzacyjny z 2026-09-05: użytkownik zaakceptował jeden dodatkowy
cykl PC-01-INTEGRATION, maksymalnie 60 minut, bez treningu i scoringu.
Wiążący zapis: research/laboratory/PC-01-EXTENSION-20260905-V1.json.
Nie zmienia to pierwotnego rozliczenia 2/2 ani kontraktu modelu i danych.
Po zakończeniu dodatkowego cyklu wymagany jest raport i nowa decyzja;
ta zgoda nie aktywuje kohorty ani nie uruchamia eksperymentu.

Kolejna, oddzielna zgoda „zatwierdzam etap” obejmuje aktywację nowej kohorty
pc01_byte_lm_learning_measurement_v1 i dokładnie jedną prerejestrowaną próbę
pc01_byte_gpt_v1, dev seed 1103. Zapis: PC-01-ACTIVATION-20260905-V1.json.
Najpierw testy bram, freeze evaluatora i nowy certyfikat; potem rejestracja EXP,
implementacja modelu i jeden run. Limity 1200 s fit / 1800 s worker pozostają
stałe. Crash/timeout zostaje wynikiem inconclusive, bez automatycznej ponownej
próby. Nie otwieramy serii finalnej ani WT-01. Pierwotny restart, 2/2 + 1/1
zamkniętych cykli oraz wszystkie wyniki pozostają zachowane. Po próbie: decyzja.

Po awarii EXP-20260905-0001 użytkownik zatwierdził wyłącznie naprawę telemetrii
i testy równoczesnego odczytu/zapisu. Plan PC-01-TELEMETRY-REPAIR-V1.json oraz
append-only READ-ADDENDUM opisują kontrolę błędów obu stron. Model, dane,
recepta i limity pozostają bez zmian. Maintenance i zakaz scoringu obowiązują
także po udanych testach. Ponowny dev wymaga nowej decyzji i nowej prerejestracji.

## 5. Etap WT-01 — wyjaśnienie dodatniego wyniku

Warunek wejścia: R0 gotowe, PC-01 interpretable albo jawna decyzja po jego
niepowodzeniu; dokładnie odzyskane historyczne źródło i cały dependency bundle.

Preregisterujemy factorial 2x2x2: rekurencja/history delta, aktualizacja RLS,
clipping/bound. Dla usunięcia rekurencji zachować jawnie zdefiniowaną
jednokrokową/persistence kontrolę; nie zmieniać innych stałych, danych,
harmonogramu ujawnień ani rachunku kosztu. Jeżeli dana interakcja zmienia
znaczenie operacji, wyjaśnić to przed wynikiem, zamiast nazywać jej wynik
automatycznie czystą ablacją. Dodać algebraicznie równoważny klasyczny VAR(2)
i uczciwie rozliczony właściwy baseline nieliniowy, jeśli uzasadnia go pytanie.

Osobno: reprodukcja historyczna na znanych danych (diagnostyka), nowe niezależne
ślady z tej samej klasy (replikacja), zamrożona trudniejsza operacja (adversarial).
Minimum 3 seedy nie zastępuje niezależnych śladów. Prerejestrować rozmiar efektu,
stabilność, recovery po zmianie, okna/horyzonty, pełny koszt i pamięć. Nie stosować
progów z arbitralnego obcego świata do odrzucenia wyniku WT.

Wnioski rozłączne: (a) RLS/ograniczenie wystarcza — klasyczne wyjaśnienie;
(b) dodatkowy izolowany efekt dynamiki — wąska zasada, nie transfer ogólny;
(c) przewaga znika na nowych śladach — zamknąć tę wersję;
(d) kontrola/evaluator nie działa — wynik nierozstrzygający.
Nie wyciągać ze samej jakości wniosku o niższym koszcie.

Limit: 2 cykle serwisowe do zamrożenia kontraktu i danych, maks. 2 jawne próby
dev; potem jeden zamrożony factorial i, tylko przy dodatnim efekcie, jedna
niezmieniona replikacja i jeden prerejestrowany adversarial. Każdy scored
eksperyment tylko przez runner, jeden na cykl. Dokładne budżety przed rejestracją.

## 6. Obowiązkowy przegląd po pierwszym pakiecie

Po R0 + PC-01 + WT-01: jeden przegląd bez scoringu, tabela pytanie/dowód/
ograniczenie/koszt/decyzja. Nie wymagamy pozytywnego WT, aby uznać poprawną
kalibrację za użyteczną. Nie przechodzimy automatycznie do integracji.

Jeśli pozytywna kontrola nie działa, naprawić aparaturę w nowej wersji albo
zatrzymać etap; nie falsyfikować całej rodziny. Jeśli działa, a kandydat nie,
zamknąć testowaną wersję i ocenić najtańsze następne pytanie. Dalszy budżet
i przejście do prototypu wymagają osobnej decyzji użytkownika po przeglądzie.

## 7. Dopiero potem: jeden system pamięć–aktualizacje–kompozycja

Małe zadanie z naturalnopodobnym wejściem, zależnościami i zmianą istniejących
faktów, nie tylko append-only. K to jawna liczba zapisanych informacji, D
zmieniamy niezależnie. Sprawdzamy podobne distraktory, niewidziane kompozycje,
retention i prawdziwy koszt od wejścia do odpowiedzi.

Baseline: kompetentny gęsty transformer, neural + retrieval oraz mocne klasyczne
rozwiązanie z identycznie legalnymi informacjami. Koszt obejmuje encoder/decoder,
retrieval, budowę indeksu, trening, aktualizacje, cache, pamięć i scenariusze reuse.
Elementy typu stos, indeks lub WT dołączamy wyłącznie, kiedy wymagają ich zadanie
i dowody. Nie budujemy automatycznie „zwycięzcy = suma wszystkich części”.

Zwiększenie inwestycji dopiero po powtarzalnej przewadze przy dopasowanej
jakości, na szerszej skali i niezależnych danych, bez ukrytych kosztów.

## 8. Kontrole i gotowość do startu

```powershell
uv run nextai doctor
uv run nextai lab status
uv run nextai provenance --experiment EXP-20260831-0007 --candidate wt_candidate_under_test --revision 4952515
uv run pytest
```

PASS infrastruktury oznacza gotowość do pierwszego cyklu PC-01-CONTRACT.
Nie oznacza, że model już wytrenowano ani że można ominąć maintenance.
Nie uruchamiamy tu eksperymentu, automatyzacji, publikacji ani drugiego laboratorium.
Historia drugiego worktree NEXTAI-LAB-B pozostaje poza zakresem.

Każde zakończenie cyklu zapisuje ID, ścieżki/hash, obiektywne obserwacje,
niepewność, interpretację, decyzję, budżet/integralność i dokładny następny krok.
Prawdopodobieństwa przekonań nie są funkcją nagrody.

## Źródła metodologiczne

- [Git: jawne EOL](https://git-scm.com/docs/gitattributes) — mechanika checkoutu.
- [MLPerf Inference](https://arxiv.org/abs/1911.02549) — rozdzielone scenariusze
  pomiarowe i ograniczenia jakości; zastosowanie tutaj jest naszą decyzją.
- [Deep RL at the Edge of the Statistical Precipice](https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html)
  — ostrożność wobec niewielu uruchomień; nie gotowy dowód dla NEXTAI.
- [TinyStories](https://arxiv.org/abs/2305.07759) — możliwy kierunek kalibracji,
  nie dokonany wybór danych; syntetyczne pochodzenie i licencję trzeba ujawnić.
