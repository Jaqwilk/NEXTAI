# MUC v2: końcowy wynik i stan etapu

**Decyzja naukowa: DISCARD tej zamrożonej receptury. Eksperyment jest kompletny; końcowa weryfikacja operacyjna pozostała niedokończona po awarii.**

Na pięciu świeżych sparowanych seedach ranking wzrósł z 9,333% do 17,333% (+8,000 pp; CI 97,5% [−3,869; +19,869] pp). Główne dense UNKNOWN spadło z 30,000% do 15,852% (−14,148 pp; CI 97,5% [−55,633; +27,336] pp). Oba CI obejmują zero. Znana abstencja wzrosła z 0% do 9,481%, przekraczając zamrożoną bramkę +2 pp. Nie potwierdzono łącznej poprawy wyboru faktów i rozpoznawania braku odpowiedzi.

Model,4096 par,192 kroki i próg0,5 pozostały niezmienione. Wszystkie 11 ról/135 prób zakończyły się poprawnie. Kontrola symboliczna uzyskała100%. Nie połączono starych wyników lub seedów,nie zastąpiono żadnej pary i nie wykonano retry. Pełna analiza oraz interpretacja zachowują również niekorzystne jednostki i różnicę między dense UNKNOWN a opisowym E2E UNKNOWN.

| Koszt | Wartość |
|---|---:|
| Nadzorowany fit wszystkich ról | 115.413948/3600 s |
| Pełna praca workerów | 626.965224 s |
| Kontroler z rejestracją | 1041.929174 s |
| Przed- i poeksperymentalne kontrole | 512.644879/1800 s |
| Pełny zegar etapu do rozliczenia | 3562.605 s (59.38 min) |
| Konserwatywnie rozliczony cały etap | 3863/14400 s (64.38 min) |

Pomiar zegara obejmuje wszystkie testy,analizę,dokumentację,administrację i zachowane błędy. Rozliczenie dodaje 300s na końcowy zapis,synchronizację Git i przekazanie raportu. Nie sumujemy ponownie fitu,workerów i kontrolera: to zagnieżdżone granice kosztu. Energia i pieniądze nie były mierzone.

Przed treningiem przeszło67/67 testów zgodności oraz Doctor i Lab. Niezależny przegląd wyników nie wykazał błędów metryk,CI,parowania,świeżości lub kosztów. Po wykonaniu w klonie ponownie odtworzono analizę,potwierdzono hashe archiwum,prefiksy rejestrów i niezmieniony portfel B.

Końcowy test cyklu życia zakończył się FAIL: `literature review is due: 6 completed experiments since the last review (cadence 6)`. Nowy wynik zwiększył licznik zakończonych eksperymentów do123; ostatni przegląd pozostaje przy117. Nie zmieniono licznika ani rytmu przeglądów. Po tym pierwszym błędzie zatrzymano dalszą sekwencję; nie uruchomiono postrun Doctor/Lab i nie powtórzono testu. Ta bramka dotyczy obowiązków utrzymania projektu po eksperymencie; źródła i wyniki naukowe zostały wcześniej poprawnie zamrożone i sprawdzone.

Zachowano również administracyjny AssertionError dotyczący manifestu dokumentacji: helper błędnie oczekiwał CURRENT_STATUS.md w chronionych wpisach. Nie powtórzono helpera; osobny zapis uzgodnił istniejące bajty i potwierdził brak zmian kodu naukowego. Pełne dane obu awarii oraz oryginalne bajty diagnostyczne są w archiwum.

Niedokończony zakres: końcowe Doctor/Lab oraz należny przegląd literatury. Dalsze prace wymagają osobnego zakresu; nie ma upoważnienia do ponowienia tego eksperymentu. W tej sesji nie otwierano WT8–9,przyszłych writerów ASM/HAR,nie dodawano architektur,nie używano zewnętrznych modeli/API i nie zmieniano harmonogramu.

Historia i portfel B są nienaruszone:1/12 rejestracji,20098,55024020007/72000s; rezerwa7 rejestracji/47000s. Szerszy cel transferu i prototypu pozostaje aktywny. Obecna konfiguracja jest przywrócona do parent ASM01 maintenance,scoring=false.

Końcowy zapis kosztów: `research/laboratory/MUC02-REPLICATION-FINAL-ACCOUNTING-V1.receipt.json`. Oryginalny raport: `research/analyses/EXP-20261006-0001.md`; interpretacja: `research/analyses/EXP-20261006-0001-interpretation-V1.md`.
