# Przygotowanie laboratorium — LAB-PREP-20260904-0001

## OBSERVATION

Pełny plan zapisano w research/LAB_PLAN.md. AGENTS.md, program, README,
roadmapa, metryki, instrukcja wybudzeń i konfiguracja wskazują teraz protokół v3
i kolejkę PC-01 -> WT-01 -> przegląd -> warunkowy prototyp. To reset strategii,
nie zaliczenie dawnego etapu zdolności G2. Scoring jest zablokowany zarówno przez
maintenance, jak i chroniony kontrakt przygotowania. Nie wykonano eksperymentu,
treningu, losowania scoring seedów ani powtórki CAL-20260901-0001.

Naprawy infrastruktury: jawne EOL z trzema wyjątkami, kontrola świeżości raportu
po treści, odtwarzanie historycznego source bundle po hashu oraz lab status.
Pełny stary protokół zachowano byte-for-byte; stary manifest zarchiwizowano.
Pierwotny certyfikat preflight w research/checks/ pozostał bez zmian. Nowy
certyfikat jest oddzielny w research/laboratory/. Uaktualniono pięć odwołań do
hasha testu baseline'u, ponieważ jego asercja aktywnego statusu zmieniła się na
maintenance. Kod algorytmów i test ich zachowania numerycznego nie zmieniły się.

Walidacja:

- pełny zestaw: 689 passed, 0 failed, 72.17 s;
- doctor: PASS, 837 chronionych plików, 99 wyników EXP, 0 pending plans;
- dwie odtworzone kopie z core.autocrlf=false/true: doctor PASS i po 47 testów;
- provenance odzyskał 3 historyczne zależności WT z commitu 4952515;
- hashe wszystkich wcześniejszych planów, wyników, analiz, przeglądów, checks,
  corpora, audits i ledgerów pozostały identyczne przed dopisaniem tego zdarzenia;
- archiwum protokołu ma oryginalny SHA-256 8e03fdd87da5b58dfbb3165c1225f862b255f2c11678c6128c0c137b6d5e15cd.

Pierwszy pełny test miał dwa błędy migracji (stary certyfikat i asercja active);
obie przyczyny naprawiono, zamiast wyłączać kontrole. Pierwsza kopia Git poprawnie
odmówiła pełnego doctor z powodu brakujących, ignorowanych danych SuiteSparse.
Same 837 hashy chronionych plików już przechodziło. Następnie skopiowano istniejące
lokalne payloady (227732138 B na kopię); benchmark zweryfikował ich hashe. Danych
nie pobierano. To testy checkoutu na Windows, nie uruchomienie natywnego Linux.

Bootstrap sprawdza miejsce przed instalacją i po niej, używa uv.lock, oddziela
cache na mierzonym woluminie i wywołuje doctor. Brakujące rozmiary torch w locku
uzupełniono osobnym plikiem metadanych z HEAD oficjalnego mirrora; żaden wheel
nie został pobrany. Oszacowanie środowiska/cache to 31552487876 B plus 10 GiB
rezerwy. Nie wykonano świeżej instalacji w chmurze; wymaga dostępnego uv i danych.

## INTERPRETATION

Repozytorium jest gotowe do pierwszego kroku PC-01-CONTRACT. Mierzalne usterki
EOL i mtime z audytu usunięto bez zmiany starych wyników. Historyczna interpretacja
WT może już odwoływać się do właściwego kodu. Nie ma jeszcze nowego wytrenowanego
modelu ani zamrożonej kohorty kalibracyjnej; przygotowanie nie jest jej sukcesem.

## CONFIDENCE

Wysoka dla spójności lokalnego harnessu, zachowania historii i naprawy checkoutu.
Niezweryfikowane: natywny Linux, świeża instalacja Cloud Agent, osiągalność
pozytywnej kontroli w przyszłym budżecie, ekonomiczna/ogólna przewaga mechanizmu.

## ALTERNATIVE EXPLANATIONS

Testy infrastruktury nie mierzą czułości na użyteczny efekt uczenia. Udany
checksum lub brak wyjątku nie zastępuje treningu ani sensownej kontroli dodatniej.
Różnice urządzeń i brak danych na nowym komputerze nadal wymagają jawnej obsługi.

## DECISION

KEEP przygotowanie; nie promować architektury. Zapisano granice i skończone
budżety etapów. Harmonogramu nie uruchomiono/nie zmieniono, niczego nie wysłano
do GitHub. Drugie laboratorium/worktree nie było modyfikowane.

## NEXT DISCRIMINATING EXPERIMENT

Najpierw PC-01-CONTRACT: jeden cykl projektowania bez treningu/scoringu, wybór
licencjonowanych lokalnych danych i kompetentnej recepty małego transformera,
zamrożenie splitów, kontroli uczenia i pomiarów, progów, budżetu, urządzenia,
scenariuszy batch=1/throughput i polityki wyniku. Dopiero nowy przetestowany
kontrakt/kohorta może otworzyć scoring. Starej kohorty nie aktywować w tym celu.
