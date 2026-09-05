# PC-01-CONTRACT-V1 — kontrola uczenia i wiarygodności pomiarów

Cykl 284, pierwszy z dwóch cykli przygotowania PC-01. To zamrożony kontrakt
projektowy, nie plan EXP, wynik eksperymentu ani zgoda na obejście maintenance.
Parametry maszynowe: `research/plans/PC-01-CONTRACT-V1.json`. Oba dokumenty są
hashowane w zdarzeniu `lab_milestone_progress`; po zamknięciu nie edytujemy ich.
Korekta wymaga nowej wersji i jawnego powodu, nigdy usunięcia poprzedniej.

## OBSERVATION

Repozytorium ma 99 historycznych wyników, żadnego nowego wyniku PC-01. Dostępne
są PyTorch 2.6.0+cu124, CUDA, BF16 i RTX 4070 z 12 878 086 144 bajtami VRAM.
Nie wykonano treningu, obliczenia jakości ani realizacji seeda eksperymentalnego.

Pobrano dokładnie 1 115 394 bajty Tiny Shakespeare z przypiętego commita
char-rnn. Limit pobrania wynosił 2 MiB; po operacji pozostało 111 753 605 120
bajtów na C:, powyżej wymaganych 10 GiB. Hashe i licencja są w
`research/data/pc01_tinyshakespeare_v1/acquisition.json` oraz `LICENSE-NOTICE.md`.
Treści korpusu nie wyświetlano; obliczanie hashy odczytało również część finalną.
Nie jest to test niedostępny dla agenta — nie wolno tak go przedstawiać.

## INTERPRETATION

Celem jest sprawdzenie aparatury: czy kompetentny, konwencjonalny model potrafi
się nauczyć i czy nasz pomiar wykrywa różnicę. Nie budujemy nowej architektury.
Nie wymuszamy przewagi nad PPM/CTW, lokalnej aktualizacji ani cross-family jako
warunku wykrycia uczenia. Tani model z gorszą jakością nie wygrywa ekonomicznie.

Źródła pierwotne: [zbiór i deklaracja MIT](https://github.com/karpathy/char-rnn/blob/6f9487a6fe5b420b7ca9afb0d7c078e37c1d1b4e/Readme.md),
[receptura nanoGPT](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/config/train_shakespeare_char.py),
[definicja modelu](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/model.py),
[procedura treningu](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/train.py).
Wybrano istniejącą małą recepturę do kalibracji, nie dlatego, że znamy wynik
porównania NEXTAI. Repozytorium nanoGPT jest archiwalnym punktem odniesienia,
nie rekomendacją najnowszego stosu. Żadne wagi ani usługi modeli nie są potrzebne.

### Dane i granice informacji

Przed pobraniem ustalono przedziały bajtowe: train [0,948084), dev
[948084,1003854), final [1003854,1115394), około 85/5/10 procent.
Bez normalizacji, tasowania, usuwania powtórzeń i okien przekraczających split.
Słownik jest stały: 256 wartości bajtu, bez uczenia tokenizera na pełnym pliku.
To jawna adaptacja receptury znakowej, nie dokładna replikacja opublikowanej straty.

Uczenie widzi tylko train, wybór checkpointu tylko dev. Część finalna nie może
być użyta do doboru progów, treningu, stopowania ani wyboru baseline'ów. W nowym
harnessie trening otrzyma wyłącznie wydzielony bufor train; kontrola dostępu ma
odrzucać próbę żądania final podczas fit. Jest to kontrola interfejsu, nie sandbox
uniemożliwiający agentowi odczyt pliku. Żadnego twierdzenia o niezależnej ślepocie.

Ocena: w każdym splicie starty 0,256,512,...; wejście do 256 bajtów, targety
przesunięte o jeden. Krótszy ostatni fragment jest liczony z maską paddingu.
Każdy target od indeksu 1 do końca splitu liczony raz. Pozycje i kontekst resetują
się w każdym oknie. NLL sumujemy po wszystkich targetach, dzielimy przez ich
liczbę i ln(2): bits per byte, mniej = lepiej. Zero pomijania trudnych fragmentów.

Jednostka danych to jeden korpus jednego autora. Fragmenty i seedy nie tworzą
niezależnych książek ani nowych domen. Powtórzenia w tekście mogą ułatwić zadanie;
nie usuwamy ich po wyniku. Nie używamy bootstrapu nakładających się okien jako
dowodu niezależnego transferu. Nie testujemy skalowania K/D na tych danych.

### Receptura i kontrola dopasowania

Model: 6 bloków pre-LN, szerokość 384, 6 głów, MLP 1536/GELU, kontekst 256,
uczone pozycje, wspólne embeddingi wejścia/wyjścia, dropout 0.2, bez biasów.
Oczekiwane 10 818 432 unikalne parametry. AdamW: LR 0.001, beta 0.9/0.99,
weight decay 0.1 dla macierzy, clipping normy 1, warmup 100, cosine do 0.0001.
Batch 64, dokładnie 5000 aktualizacji, BF16 autocast i FP32 stan/strata.
Inicjalizacja i scheduler zgodnie z przypiętym źródłem; szczegóły w JSON.
Nie stosujemy torch.compile, TF32, zewnętrznych tokenizerów, model API ani wandb.

Jawne różnice od źródła: bajty zamiast wyznaczania znaków z całego korpusu,
osobny dev i final, pełna deterministyczna ocena dev, eager zamiast compile,
niefused AdamW, wyłączone TF32 oraz dokładnie 5000 zamiast inkluzywnej pętli.
Te różnice ograniczają przenoszenie opublikowanego czasu/straty na nasz komputer.

Każde 250 aktualizacji liczymy cały dev; również stan początkowy i krok 5000.
Najlepszy wytrenowany checkpoint = najmniejszy dev bpb, remis = wcześniejszy.
Nie kończymy wcześniej na podstawie jakości. Limit czasu przed 5000 kroków
oznacza niewystarczający budżet, nie pełną negatywną kontrolę ani jej sukces.
Zachowujemy krzywą, czas, wszystkie próby, błędy i wybrany hash checkpointu.

Maksymalnie trzy próby dev z seedem 1103. Pierwsza realizuje tę recepturę.
Następne mogą naprawić udokumentowany błąd implementacji, nie przeszukiwać
hiperparametrów albo zwiększać budżet po słabym wyniku. Każda ma nową jawną
rejestrację i zachowany poprzedni wynik. Zmiana naukowej receptury wymaga nowej
wersji kontraktu, przed wynikiem, w tym samym limicie prób — nie jego wyzerowania.

### Oddzielne kontrole i progi

Kontrola przyczynowa: ten sam kod, początkowe parametry i kolejność danych;
różnicą jest zastosowanie aktualizacji wag versus zachowanie inicjalizacji.
Ocenę zamrożonego stanu wykonujemy przed treningiem, bez modyfikacji jego wag.
Skale odniesienia: uniform 8 bpb, unigram add-one i bigram add-one dopasowane
wyłącznie na train. Bigram resetuje kontekst jak transformer. Nie określamy ich
mianem najsilniejszych kompresorów; nie służą tu do ogłaszania przewagi kosztowej.

Warunki dodatniej kontroli, ustalone tutaj przez nas, nie zaczerpnięte jako
uniwersalny standard: w każdej z trzech końcowych replik trained bpb <= 3.5
oraz frozen bpb minus trained bpb >= 1.0. Dolna granica 95% przedziału t dla
średniej sparowanej poprawy musi przekroczyć zero. Raport obejmuje wszystkie
wartości, średnią, SD i zakres; dla n=3 używamy df=2, kwantylu 4.3026527299.
To skromny, zależny od założeń opis zmienności seeda na jednym korpusie.

Dodatkowy wynik kontekstowy: przewaga >= 0.1 bpb nad unigramem we wszystkich
trzech replikach. Raportować osobno, nie ukrywać braku tej przewagi, nie podmieniać
nią głównego progu ani robić z niej dowodu transferu. Nie ma automatycznej promocji.

Niezależne testy aparatury wymagane przed aktywacją:

- Znane prawdopodobieństwa w float64: uniform daje 8 bpb; rozkład z p(target)=0.5
  daje 1 bpb. Tolerancja 1e-10. Porównać niezależne sumowanie logów z metryką.
- Błędne targety na sztucznym fixture: p(poprawny)=0.99, reszta 0.01/255.
  Poprawna strata <0.02 bpb, po zamianie targetu >10 bpb. Zła wersja musi zostać
  odrzucona; nie oczekujemy określonego spadku na losowo przestawionym Shakespeare.
- Wyłączone uczenie: 100 syntetycznych kroków bez optimizer.step nie zmienia
  hasha wag; kontrola dodatnia zmiany wag sprawdzana dopiero w zarejestrowanym dev.
- Zmiana przyszłego sufiksu nie zmienia wcześniejszych logitów (eval/FP32,
  atol=1e-5, rtol=1e-5); wykryć nieprzyczynową maskę. Bez dropout w ocenie.
- Wykryć wspólny indeks w splitach, pomylone przesunięcie targetu, odczyt final
  podczas fit i wybór checkpointu według final. Celowo uszkodzone fixture muszą fail.
- Metryka po podziale batchy identyczna w FP64 do 1e-10; FP32/BF16 porównać
  na dev dla tych samych wag, różnica bpb <=0.02, inaczej precision-inconclusive.
- Testy limitów czasu/RAM/VRAM, deduplikacji seedów i niezmienności receptury
  całej serii; same testy jednostkowe nie dowodzą, że model się nauczył.

### Pomiary i koszt

Batch=1 mierzy pojedynczy następny bajt z kontekstu 256, bez KV cache. Czas od
przetworzenia bajtów wejścia przez H2D i forward do argmax i odebrania wyniku na
CPU, z CUDA synchronize przed i po. Model już załadowany; load raportowany osobno.
Throughput mierzymy osobno dla B=1,8,32, teacher forcing po 256 pozycji i odebraniu
wszystkich przewidywanych bajtów. To nie szybkość generowania autoregresyjnego.

Stałe okna dev, 20 warmupów na scenariusz, 100 pomiarów w dwóch blokach po 50,
odwrócona kolejność scenariuszy w drugim bloku. Warmupy zapisane i rozliczone
osobno, nie w percentylach. Zachować każdą próbkę nanosekund, p50/p95, liczby
wejść/wyjść i łączny throughput. Nie odrzucać wolnych próbek jako niewygodnych.
Sprawdzić rzeczywisty wynik i synchronizację; logować wersje, driver, CPU,
obciążenie, pamięć RSS oraz CUDA allocated/reserved. Bez równoległego joba GPU;
nie zamykać aplikacji użytkownika. Zmienne obciążenie ogranicza interpretację czasu.

Oddzielnie koszty pobrania/przygotowania, rozwoju, fit, selekcji, ładowania,
checkpointów i zapytania. R=1,10,100 oznacza powtórzenie pełnego workloadu
100 zapytań batch=1, nie pojedynczego pytania. Pokazać całkowity koszt i składniki;
nie wyznaczać zwycięzcy ekonomicznego bez właściwych baseline'ów i matched quality.
Operacje/MAC/FLOPs estymowane oznaczyć jako estymaty. Energia: nie zmierzono.

### Budżet i legalna ścieżka wykonania

Ten cykl zużywa 1/2 cykli serwisowych. Rezerwujemy konserwatywnie 60/120 minut
budżetu przygotowania: dokładnego początkowego zegara nie zapisano, więc nie
udajemy precyzyjnego pomiaru czasu. Pozostał jeden cykl i najwyżej 60 minut.
Prób dev 0/3; treningu 0 minut. Kolejny serwis nie może stać się nieskończoną pętlą.

Na jeden fit wraz z walidacją dev i checkpointami: 1200 sekund; na cały worker
deep: 1800 sekund i 10 GiB RSS. CUDA allocated oraz reserved <=10 GiB. Kontrole,
finalna ocena i timing muszą zmieścić się w pozostałych 600 sekundach workera.
Wszystkie dopasowywane role zwraca jeden diagnostyczny worker; bez dodatkowego
nieewidencjonowanego treningu. Maksymalnie 2 GiB danych/checkpointów PC-01 i
zawsze co najmniej 10 GiB wolnego dysku. Zachować nieudane artefakty w tym limicie.

Trzy próby dev plus trzy końcowe replikacje po maks. 20 minut = 120 minut
łącznego fit. To konserwatywnie obejmuje final w całym limicie treningu PC-01.
Replikacje końcowe są trzema osobnymi EXP, po jednym na cykl, każdy jeden seed
realizowany przez runner. Wszystkie mają identyczny zamrożony kod i recepturę.
Seedy z [10000,2147483647], różne w całej serii, bez selekcji udanych seedów.
Nie wolno nic dostrajać między wynikami końcowymi.

Aktualny deep domyślnie losuje pięć seedów, a jego limit dotyczy całego workera.
Nie wolno wcisnąć 3 x 1200 s do 1800 s albo uruchomić treningu poza runnerem.
Nowa kohorta musi jawnie implementować jeden seed na EXP i bramkę trzech różnych
replik dla wspólnego wniosku, bez zmiany historycznych polityk. Jeżeli nie da się
tego poprawnie wdrożyć w pozostałym serwisie, raportujemy blocker i kończymy etap
przygotowania; sam ten dokument nie czyni obecnego runnera zgodnym z kontraktem.

## CONFIDENCE

Wysoka: tożsamość pobranych bajtów, dostępność urządzenia i brak treningu.
Umiarkowana: przydatność opublikowanej receptury do lokalnej kontroli.
Niezweryfikowana: osiągnięcie 5000 kroków i progów jakości w 20 minut na tej
konfiguracji; sam rozmiar VRAM nie dowodzi wykonalności czasowej.

## ALTERNATIVE EXPLANATIONS

Brak poprawy może oznaczać błąd targetu, optymalizatora, maski, pomiaru albo za
mały budżet. Poprawa może pochodzić głównie z nauki statystyk marginalnych lub
powtórzeń w jednym korpusie. Ani jedna z tych sytuacji nie falsyfikuje całej
rodziny architektur. Dlatego wymagamy rozdzielonych kontroli i ograniczamy wniosek.

## DECISION

KEEP wyłącznie kontrakt do implementacji aparatury. Dodatniej kontroli jeszcze
nie uzyskano. Ważny finalny wynik ujemny zamyka tę wersję; nie naprawiamy jej na
final. Crash, limit, przeciek albo błędna kontrola oznaczają INCONCLUSIVE i jawny
raport. Dalsza zmiana pytania wymaga nowego kontraktu i świeżych danych finalnych.
Stary CAL, G1, BELIEFS, wyniki i plany pozostają bez zmian.

## NEXT DISCRIMINATING EXPERIMENT

Najpierw PC-01-HARNESS: drugi i ostatni cykl serwisowy, bez treningu/scoringu.
Zaimplementować i przetestować nowy evaluator i bramki, schemat diagnostyki,
ograniczenia workerów oraz jawne przejście kolejki. Zarchiwizować stary manifest,
zamrozić nową kohortę i certyfikat. Dopiero po ich gotowości zarejestrować EXP
przez `nextai plan new`, a następnie implementować testowany model. Pierwszym
eksperymentem będzie kontrola dev 1103: włączone uczenie kontra identyczna
inicjalizacja, bez dostępu do final, z powyższymi kontrolami i budżetem.

`restart.json` i obecne `nextai lab status` nadal wskazują początkowe
PC-01-CONTRACT; nie nadpisujemy ich chronionego kontraktu w tym cyklu. Bieżący
postęp i następny krok są zapisane append-only w `lab_milestone_progress`.
Następny serwis musi uzgodnić ten wskaźnik z historią, bez odblokowania scoringu
samym przemianowaniem statusu. Nie uruchomiono harmonogramu ani publikacji GitHub.
