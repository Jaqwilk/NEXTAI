# Audyt projektu NEXTAI i ocena postępu

Data przeglądu: 2 października 2026, Europe/Warsaw. Sprawdzony commit: `7b0ddaa0c3a31ddf19230ed3cacebbb8cc87b0bf`. Autor: Codex, na prośbę właściciela projektu. Dokument jest nowym przeglądem, nie eksperymentem, korektą historycznego wyniku ani zgodą na wykonanie kolejnego etapu.

**Werdykt: NEXTAI ma wartość jako laboratorium małych, kontrolowanych badań. Powstała użyteczna infrastruktura i kilka wąskich wyników, ale nie ma dowodu na nową architekturę przewyższającą gęste modele przy dopasowanej jakości i pełnym koszcie. Najbliższa inwestycja powinna poprawić wiarygodność pomiarów i zawęzić badane pytanie. Dalsze rozszerzanie liczby kandydatów jest obecnie słabiej uzasadnione.**

W audycie wykryto także błąd wykonania samego przeglądu: pełny zestaw istniejących testów odczytał zabronione pliki WT 8–9. Opis i odpowiedzialność są zapisane poniżej. Wyniku tych wywołań nie traktuję jako dowodu naukowego.

## OBSERVATION

### Zakres i wykonana weryfikacja

Przeczytałem obowiązujące instrukcje, kolejkę laboratorium, protokół, stan i końcowe zdarzenia. Przetworzyłem wszystkie 106 plików wyników EXP, rejestr planów i historię 59 hipotez; wydobyłem decyzje z analiz. Ręcznie prześledziłem najważniejsze dodatnie i ujemne wyniki oraz ścieżki wykonania: CLI → uprawnienia → blokada → worker → evaluator → metryki → wynik → raport. Szczególnie dokładnie sprawdziłem PC-01, WT-01 i najnowsze MUC-01.

Przeprowadziłem inwentaryzację wszystkich śledzonych plików i parsowanie AST wszystkich 715 modułów Python w `src`. Nie jest to deklaracja ręcznej kontroli każdej z 43 907 linii ani formalny dowód braku innych błędów. Archiwalne kopie kodu potraktowałem jako dokumentację pochodzenia; dane WT 8–9 nie były zamierzonym zakresem audytu.

| Weryfikacja | Wynik i znaczenie |
|---|---|
| `uv run nextai doctor` | PASS; 923 chronione pliki, 529 audytów modułów kandydatów, brak oczekującego planu. To kontrola spójności, nie poprawności każdej metryki. |
| `uv run nextai lab status` | `MUC-01-CALIBRATION-DECISION`, `scoring_authorized=false`. |
| `uv run pytest --durations=12` | 970 testów przeszło w 382,77 s. Zestaw miał niedozwolone skutki uboczne opisane w F01, więc sam PASS nie oznacza zgodności z zakresem. |
| Historyczne provenance WT | Trzy zależności EXP-20260831-0007 odzyskane po hashach z commita `4952515`; historycznego kodu w tym sprawdzeniu nie wykonano. |
| Dodatkowe małe kontrole | Potwierdzono brak walidacji liczby odpowiedzi, kumulowanie kosztów, błędne etykiety kompozycji, przejmowanie żywej blokady i brak reakcji watchdoga na STOP. |
| Zmiany repozytorium | Dodano wyłącznie ten przegląd i plik dowodowy. Kod wykonawczy, manifesty, wyniki, ledgery i stan eksperymentów pozostały bez zmian. |

[Plik dowodowy audytu](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/research/reviews/PROJECT-AUDIT-2026-10-02.evidence.json) zawiera liczności, wyniki kontroli syntetycznych i hashe dokumentów naukowych. Kontrole nie są nowymi wynikami EXP. Część istniejących testów wykonuje małe dopasowania modeli i odczyty danych, dlatego nie opisuję pełnej regresji jako pracy wyłącznie statycznej lub całkowicie bez fitu.

### Wielkość repozytorium i rzeczywisty stan badań

| Wielkość | Stan |
|---|---:|
| Śledzone pliki | 6 710 |
| Moduły Python w `src` | 715 |
| Linie kodu w `src` | 43 907 |
| Pliki w katalogu kandydatów | 531; 446 ma najwyżej 20 linii |
| Moduły w katalogu benchmarków | 107 |
| Archiwalne pliki laboratorium | 4 398; około 17,3 MB |
| Rejestracje EXP | 139 |
| Pliki wyników EXP | 106: 101 w ogólnym runnerze i 5 diagnostyk PC-01 |
| Statusy plików wyników | 89 `complete`, 16 `complete_with_failures`, 1 `inconclusive` |
| Wyniki z formalną korektą nieważności naukowej | 4; pozostają w historii |
| Hipotezy | 36 `falsified`, 22 `dormant`, 1 `testing` |
| Hipotezy `promising` lub `promoted` | 0 |
| Seedy w 101 wynikach ogólnego runnera | 90 wyników z jednym seedem; 11 z trzema |
| Wersje benchmarków ogólnego runnera | 89; aż 80 ma tylko jeden plik wyniku |

Pięć wyników PC-01 obejmuje dwie próby dev, w tym zachowaną awarię, i trzy finalne repliki. Nie należy dodawać trzech replik PC-01 do jedenastu trzyseedowych wyników tak, jakby były tym samym rodzajem jednostki. Analogicznie 33 rejestracje bez wyniku nie oznaczają 33 udanych dodatkowych eksperymentów; historia zachowuje terminalne unieważnienia i brak pending planu.

531 plików kandydatów nie oznacza 531 niezależnych architektur. Duża część to krótkie klasy ustalające rolę lub parametr wspólnego rdzenia. Część identyczności jest pożądana: umożliwia uczciwe ablacje, czyli porównania różniące się jednym czynnikiem.

### Co faktycznie osiągnięto

| Obszar | Zaobserwowany wynik | Uzasadniony wniosek | Czego wynik nie dowodzi |
|---|---|---|---|
| Indeksy, routing, cache, biblioteki programów | W wielu małych zadaniach uzyskano lokalny dostęp lub oszczędność powtórnego wykonania. Klasyczne kontrole często odtwarzały efekt taniej. | Poprawny adres i stabilny klucz są ważniejsze niż sam deklarowany brak zależności kosztu od K. | Odkrycia ogólnego uczonego mechanizmu tańszego niż istniejące algorytmy. |
| Pushdown, EXP-20260901-0041/0042 | W replikacji 144/144 całych sekwencji domknięcia było poprawnych; ablacje ograniczonego stosu nie rozwiązywały sekwencji. | Wąski efekt stanu stosowego i ekstrapolacji głębokości. | Ogólnej zdolności rozumowania, automatycznego odkrycia całej struktury push/pop lub dominacji ekonomicznej. |
| Pushdown, EXP-20260901-0044 | 0/144 poprawnych sekwencji przy odtwarzaniu zamaskowanych operacji push z przyszłych domknięć. | Zamrożona reguła była jednostronnym rozwiązaniem konkretnej operacji. | Że wszystkie modele ze stosem albo cała rodzina uczenia struktur są bezwartościowe. |
| R0 | Naprawiono rozliczanie pochodzenia kodu, EOL i świeżość raportu zależną od treści. Obecne provenance działa. | Duży postęp odtwarzalności lokalnej. | Pełnej odtwarzalności na natywnym Linux, której ten audyt nie uruchamiał. |
| PC-01, EXP-20260905-0003/0004/0005 | Uczony transformer: 2,4809–2,5144 bpb; nieuczony: około 8,04–8,12 bpb. Średni kontrast 5,5741 bpb; raportowana dolna granica t 5,4392. | Aparatura potrafi wiarygodnie wykryć zwykłe uczenie gradientowe na jednym korpusie. | Nowej architektury, transferu między korpusami lub przewagi nad równie dobrym rozwiązaniem klasycznym. |
| WT-01, EXP-20260906-0001 | Kontrast rekurencji 0,16279 NRMSE przy progu 0,03343; 162 stabilne próby; VAR(2)/ARX zgodny do 3,55e-15. | Dodatni efekt ma kompletne klasyczne wyjaśnienie. | Nowości, niezależnej replikacji fizycznej lub tańszej inferencji. Query work wzrosło z 470 do 22 560. |
| MUC-01, EXP-20260906-0002 | Symboliczny graf: 100%; pełny skan z readerem: 18,98%; retrieval z readerem: 75,51%; wymagano 85% dla kontroli dense. | Dokładna receptura uczonych kontroli zawiodła. Zadanie jest łatwe dla jawnej mapy relacji. | Porażki pamięci delta, której nie zaimplementowano, ani uczciwego porównania z kompetentnym pełnym dekoderem. |

Źródła: [seria PC-01](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/research/analyses/PC-01-FINAL-SERIES-V1.md), [replikacja pushdown](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/research/analyses/EXP-20260901-0042.md), [wariant przeciwny pushdown](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/research/analyses/EXP-20260901-0044.md), [WT-01](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/research/analyses/EXP-20260906-0001.md), [MUC-01](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/research/analyses/EXP-20260906-0002.md).

PC-01 zużył 2394,27 z 7200 sekund rozliczonego fitu, wliczając zachowaną awarię; same trzy finalne treningi trwały 893,84 s. Jest to rzeczywisty postęp pomiarowy. Nie wolno z liczby cykli, plików lub hipotez wyliczać procentowej drogi do następcy LLM.

### Potwierdzone błędy i luki

P1 oznacza problem do usunięcia przed kolejnym uruchomieniem korzystającym z danej ścieżki. P2 oznacza istotną poprawkę przed użyciem danego pomiaru lub kontroli do nowego wniosku. Priorytet nie jest stwierdzeniem, że błąd wystąpił we wszystkich historycznych wynikach.

**F01 P1 — Pełna regresja omija aktualne ograniczenia danych.**

[Test historycznego WT](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/tests/test_wt_local_credit_v4.py:46) wywołuje bezpośrednio `v3.run_suite` i `v4.run_suite` dla `wt_persistence_v1`. Obie ścieżki trafiają do [starego evaluatora](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/benchmarks/heldout_wt_changepoints_prequential_v1.py:241), który używa `TEST_SEEDS=(8,9)`. Dodatkowo starsze testy `verify_static_contract` haszują wszystkie dziesięć plików. Są poza kontrolą uprawnień CLI.

Ten test przeszedł podczas niniejszego audytu, więc odczyt plików 8–9 i wykonanie na nich historycznej kontroli nastąpiły. Powinienem był wcześniej wykluczyć te testy. Zakomunikowałem błąd użytkownikowi po jego wykryciu; nie uruchamiałem później dalszych testów z dostępem do danych. Nie utworzono EXP, nie wykorzystuję uzyskanych w pamięci metryk i nie twierdzę, że zachowano zakaz dostępu. To także wskazuje, że dawnego sformułowania „pełna regresja przeszła, pliki 8–9 nieotwarte” nie można automatycznie uznawać za prawdziwe bez sprawdzenia ówczesnej listy testów.

Poprawka: domyślny zestaw testów powinien używać fixture'ów syntetycznych. Testy z realnymi danymi muszą mieć jawny zakres i osobny wybór. Ograniczenie plików należy sprawdzać na najniższej wspólnej ścieżce odczytu, także przy haszowaniu i bezpośrednich wywołaniach bibliotek. Samo dodanie markera bez egzekwowania zakresu nie wystarczy.

**F02 P1 — MUC może otrzymać 100% mimo brakujących odpowiedzi.**

[Scorer MUC](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/benchmarks/mutable_contact_ledger_v1.py:46) nie sprawdza długości `answers`. Następnie używa `zip(predictions, expected)`, który ucina porównanie do krótszej listy. Na syntetycznej próbce czterech pytań system zwracający tylko trzy poprawne odpowiedzi otrzymał `accuracy=1.0`, `query_count=4` i `status=complete`. Przy wielu światach mogą również przesunąć się przypisania odpowiedzi do targetów i kategorii.

Poprawka: sprawdzić liczbę i format odpowiedzi osobno dla każdego świata, przed ich scaleniem; wymagać dokładnej liczby światów, komórek i targetów. Brakująca odpowiedź musi dać jawnie określony błąd protokołu albo porażkę. Obecne trzy role zwykle zwracają po jednej odpowiedzi na pytanie; kontrola wykazała lukę, nie dowód zawyżenia wszystkich zapisanych accuracy.

**F03 P1 — Koszt MUC miesza komórki, zapytania, kroki i całe przebiegi.**

[LearnedSystem.cost_report](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/muc01_baseline_core.py:140) uśrednia historię wszystkich sesji, a jeden system jest używany dla wszystkich dziewięciu komórek. Koszt K=512 zależy zatem od wcześniej wykonanych K=32 i K=128. `query_ops` jest dopisywane w `_rank` na jeden krok relacji, ale nazwane średnim kosztem zapytania. D=4 nie jest przez ten licznik uczciwie porównywane z D=1.

[SymbolicSystem.cost_report](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/muc01_baseline_core.py:236) zwraca skumulowane operacje jako `mean_query_ops`. Dwie identyczne sesje po jednym pytaniu dały kolejno 1 i 2. W historycznym MUC pierwsza komórka D=1 ma 240 zamiast jednego odczytu mapy na pytanie. Wynik wylicza nawet dodatni wykładnik K około 0,567 dla kontroli o odczycie mapy niezależnym od K przy stałym D. To artefakt rachunku, nie prawo skalowania.

[Wzory R1/R4/R16](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/benchmarks/mutable_contact_ledger_v1.py:75) nie dodają fitu ani pełnych kosztów wyszukiwania i przetwarzania tekstu; mieszają sumaryczny build z kosztami średnimi. Samo zapisanie `fit_ops` w osobnym polu nie oznacza, że został on uwzględniony w amortyzacji. Estymator pracy transformera nie uwzględnia m.in. długości sekwencji i pełnej pracy bloków. `state_bytes` uczonych ról obejmuje parametry, pomijając przechowywane wiersze i historię sesji; RSS całego procesu jest inną, szerszą wielkością.

Poprawka: jasno zdefiniować jednostkę workloadu i granice pomiaru; zapisywać osobne liczniki dla fitu, świata, aktualizacji, kroku oraz pełnej odpowiedzi; używać różnic liczników na granicach komórek. Test kosztu musi wykazać niezmienność przy zmianie kolejności komórek. Historyczne krzywe kosztu MUC i jego rachunek R nie nadają się do porównania ekonomicznego. Ograniczenie jest szersze niż wskazana w starej analizie sama normalizacja kontroli symbolicznej.

**F04 P1 — Raportowane p95 MUC nie jest p95 pojedynczego zapytania.**

[Evaluator](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/benchmarks/mutable_contact_ledger_v1.py:45) mierzy obsługę 16 pytań, dzieli czas przez 16 i kopiuje uzyskaną średnią szesnaście razy. Percentyl takiej listy opisuje średnie czasu na pytanie w poszczególnych światach, nie ogon opóźnienia pojedynczych odpowiedzi. Wolne pytania zostają wygładzone. Nie zapisano surowych czasów umożliwiających odzyskanie prawdziwego p95. Dodatkowo [agregator](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/metrics.py:182) uśrednia p95 komórek; średnia percentyli także nie jest percentylem połączonej próby.

Poprawka: mierzyć pojedyncze odpowiedzi i przepustowość oddzielnie, zapisywać próbki oraz sposób rozgrzewki i synchronizacji. Zachować starą metrykę pod dokładną opisową nazwą, bez przypisywania jej interpretacji B1 p95. PC-01 ma już znacznie lepszy wzorzec rozdzielonych scenariuszy i walidacji próbek.

**F05 P1 — Ogólny watchdog nie reaguje na STOP lub PAUSE podczas pracy.**

[Pętla nadzorująca](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/runner.py:323) kontroluje tylko czas i RSS. Bramki STOP/PAUSE działają przed rozpoczęciem; nie są ponownie sprawdzane podczas pracy ani przed każdym kolejnym kandydatem. Syntetyczny proces, który tworzył STOP po starcie, zakończył się z `status=complete` bez żądania zatrzymania. Nie uruchomiono w tej kontroli prawdziwego workera.

Poprawka: sprawdzać bramkę podczas monitorowania i pomiędzy rolami, zachować rezultat przerwania, zapewnić sprzątanie drzewa procesów również przy przerwaniu procesu nadrzędnego. [Supervisor PC-01](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/pc01_execution.py:353) pokazuje już rozwiązanie wielu z tych problemów. Dwie ścieżki wykonania mają obecnie różne gwarancje.

**F06 P1 — Wiek pliku pozwala przejąć blokadę żywego procesu.**

[RunLock](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/ledger.py:219) po przekroczeniu `stale_seconds` przenosi blokadę, nie sprawdzając życia i tożsamości właściciela. Test w katalogu tymczasowym potwierdził jednoczesne wejście dwóch kontekstów; po wyjściu wewnętrznego plik blokady zniknął, choć pierwszy kontekst nadal działał. `__exit__` nie weryfikuje, czy usuwa własny token blokady.

Ma to realny scenariusz: limit stale wynosi 7200 s, a limit quick to 7200 s na kandydata; cały wielokandydatowy run może legalnie trwać dłużej. Ponadto [kontrola istnienia wyniku](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/runner.py:526) jest wykonywana przed uzyskaniem blokady i nie jest powtarzana wewnątrz sekcji krytycznej.

Poprawka: blokada z jednoznaczną tożsamością właściciela, sprawdzanie żywego procesu i czasu jego utworzenia, usuwanie tylko własnej blokady oraz ponowienie sprawdzeń terminalności po wejściu. Nie ma dowodu, że doszło wcześniej do równoległego podwójnego EXP; wykazano podatność mechanizmu.

**F07 P2 — Zbiór treningowy MUC jest obcinany przed większymi K i ma sprzeczne etykiety.**

[Pętla tworząca pary](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/muc01_baseline_core.py:86) bierze pierwszy prefiks do 4096 przykładów. Z przygotowanych 405 światów dochodzi tylko do 52: wszystkich 45 dla K=32,D=1 i początku K=32,D=2. W tym prefiksie występują jedynie podmioty ET000–ET003. Dane dla K=128 i K=512 nie trafiają do uczenia. Wymieszanie kolejności po obcięciu nie rozwiązuje problemu. Dev jest przyjmowany, ale wykorzystywany jedynie do raportowania jego liczności.

Wybór przykładu negatywnego przesuwa indeks tylko raz. Ponieważ sąsiednie wpisy mogą być starą i nową wersją tego samego klucza, 25 z 4096 wygenerowanych par ma negatywną etykietę dla identycznego podmiotu i relacji. To potwierdzono przez odtworzenie wyboru danych, bez treningu. Sam ten niewielki odsetek nie wyjaśnia ilościowo całej porażki; brak pokrycia danych jest oddzielnym, większym problemem.

Poprawka: prospektywnie określone próbkowanie z każdej komórki, kontrola zasięgu encji, konstrukcja negatywów z potwierdzoną nierównością klucza i testy jakości wyłącznie na dozwolonym dev. Nowe uczenie wymaga osobnego kontraktu; nie należy poprawiać receptury i ponownie używać starego wyniku jako finalnego testu.

**F08 P2 — Etykieta niewidzianej kompozycji nie odpowiada generatorowi.**

[Dobór relation_pool](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/muc01_task.py:82) wybiera `HELDOUT_TUPLES` dla wszystkich finalnych pytań D>1, natomiast `unseen_composition` oznacza tylko pierwsze osiem. Na ustalonej próbce testowej K=128,D=4,seed=12345 czternaście pytań używało dokładnych heldout tuples, lecz tylko osiem miało flagę; sześć było niewidzianych, ale nieoznaczonych. Dwa UNKNOWN dodatkowo zmieniają końcową relację na violet. Flaga jest też skorelowana z pozycją i grupą aktualizacji.

Poprawka: oddzielnie wybierać pule seen/unseen, a etykietę wyliczać z faktycznej relacji i jawnego rozdziału train/test. Test ma sprawdzać semantykę podziału, nie tylko sumę ośmiu flag. Ogólna accuracy nie zmienia przez to automatycznie wartości, ale nie można traktować istniejącego pola jako czystego kontrastu generalizacji kompozycyjnej.

**F09 P2 — Certyfikat uczonych baseline'ów sprawdza parser zamiast modelu.**

Obie uczone role MUC w [rejestrze semantyki](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/config/baseline_semantics.json:881) mają jako test conformance wyłącznie `test_public_parsers_reject_non_grammar_and_parse_legal_text`. Test nie wykonuje ich forward, retrievalu ani treningu. Dlatego zielony certyfikat nie dowodzi realizacji deklarowanej metody, poprawności par uczących ani jakości kontroli.

Nazwa `bm25_iterative_reader_v1` jest ponadto myląca: [ranking](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/muc01_baseline_core.py:172) to stałe wagi 3 i 2 za zgodność dwóch pól, potem sortowanie po czasie. Nie implementuje częstotliwości dokumentowej, normalizacji długości ani nasycenia częstości BM25. `dense_transformer_v1` to transformerowy klasyfikator zgodności par w ręcznie zadanej pętli przechodzenia po relacjach, a nie pełny autoregresyjny model odpowiadający na cały tekst. To drugie uproszczenie zostało uczciwie ujawnione w planie aktywacji, więc nie nazywam go ukrytym naruszeniem planu.

Poprawka: jawnie nazwać i testować rzeczywiste algorytmy; do następnego eksperymentu dodać testy semantyczne rankingu, wymiarów, masek, liczników, negatywnych par i generowania UNKNOWN. Oddzielić certyfikat techniczny od potwierdzenia kompetencji na dev.

**F10 P2 — Raport usuwa frontier kompresji przez zły próg accuracy.**

[Rozpoznawanie zadań loss w raporcie](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/report.py:69) pomija prefiks `heldout_repository_sequence_`, który ogólny runner uwzględnia. Raport stosuje więc próg accuracy 0,95 do przewidywania bajtów. W EXP-20260901-0062 PPM ma accuracy około 0,455 i 3,3508 bpb; jest zapisany na frontier w wyniku, ale jego znacznik w REPORT jest pusty. To rzeczywista rozbieżność między wynikiem a wygenerowanym widokiem, nie dowód pogorszenia modelu.

Poprawka: jeden kontrakt kwalifikacji do porównania, odczytany z zamrożonej tożsamości badania. Nie dobierać kryterium użyteczności z aktualnego globalnego progu ani z rozbieżnych list prefiksów. Dodać sprawdzenie zgodności raportu z historycznym wynikiem dla v6. Metryki bpb powinny być widoczne w tabelach zadań kompresji.

**F11 P2 — Nowy prywatny generator nie został objęty audytem granicy importów.**

[Lista zakazanych modułów](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/audit.py:14) nie zawiera `muc01_task`, chociaż moduł udostępnia generator, poprawne odpowiedzi i podział światów. W tymczasowej strukturze plików kandydat importujący `split_worlds` przeszedł audyt AST. Kandydata nie wykonywałem. Seed trafia do systemu, więc takie API może umożliwić odtworzenie prywatnych odpowiedzi.

Nie stwierdziłem tego importu w rzeczywistych trzech rolach MUC ani użycia odpowiedzi przez te role. Jest to luka kontroli, nie zarzut przecieku w zapisanym wyniku. Poprawka: oddzielić publiczne typy od prywatnego generatora i testować wszystkie nowe granice. Audyt AST pozostaje pomocą w kontroli zaufanego kodu, nie pełnym sandboxem.

**F12 P2 — Gwarancje zasobów MUC są słabsze niż zatwierdzony zakres.**

Plan aktywacji deklaruje limit VRAM 11 GiB oraz fit 1200 s. Ogólny supervisor kontroluje RSS i czas całego procesu; fit jest ograniczany współpracująco przez model, a VRAM nie jest sprawdzany na tym poziomie. `fit_peak` po treningu nie zastępuje ograniczenia alokacji i nie obejmuje automatycznie późniejszego szczytu inferencji. PC-01 ma osobny watchdog, telemetrię oraz ograniczenie alokatora.

Zapisany MUC nie wykazał przekroczenia limitu; raportowane zużycie było małe. Problemem jest niewystarczająca egzekucja przyszłych uruchomień. Poprawka: wykorzystać mały wspólny mechanizm nadzoru dla nowych kohort, z zachowaniem historycznych adapterów. Nie kopiować kolejnej niezależnej implementacji samych deklaracji budżetu.

**F13 P2 — Dokumentacja aktualnej kolejki i część metadanych są niespójne.**

README wskazuje PC-01, AGENTS i program wskazują REVIEW-01, a najnowszy LAB_PLAN oraz kod wyznaczają `MUC-01-CALIBRATION-DECISION`. W jednym dokumencie pozostaje kilka nagłówków „Aktualny”. Doctor nadal ostrzega o wyczerpaniu etapu PC-01 także wtedy, gdy bieżącą decyzją jest MUC. Kod w tej chwili blokuje scoring poprawnie, ale człowiek lub kolejny proces może wybrać błędną instrukcję.

Jest również anomalia czasu: zapis zgody MUC ma `created_at=2026-09-06T08:00:00Z`, podczas gdy plan EXP utworzono o 00:31:36Z, a run rozpoczęto o 00:35:42Z. Git pokazuje obecność zgody w commicie freeze przed rejestracją, więc nie jest to dowód działania bez zgody; jest to błędna chronologia w metadanych, wymagająca jawnego wyjaśnienia.

Poprawka: jedna zwięzła projekcja aktualnego stanu, wskazująca aktywną decyzję i źródła uprawnień; historyczne dokumenty zachować. Datę wyjaśnić nowym zdarzeniem, bez przepisywania zamrożonej zgody. Nie przekształcać porządkowania dokumentacji w nowe uprawnienia.

### Dodatkowe ograniczenia

- [Worker ogólny](/C:/Users/NATAN/Documents/ChatGPT/NEXTAI/src/nextai_autoresearch/worker.py:20) dostaje całą listę triali dopiero po powrocie `run_suite`; przy wyjątku zapisuje `trials=[]`. Przerwanie późnej komórki może utracić wyniki wcześniejszych komórek tego kandydata. W przyszłej wersji potrzebny jest prosty zapis postępu po komórce. Nie należy dopisywać brakujących historycznych wartości z pamięci lub po powtórzeniu.
- Uczone MUC przechowuje wszystkie sesje w `self.sessions`. To zwiększa pamięć przez cały run, a modelowy `state_bytes` tego nie ujmuje. Do nowych pomiarów wystarczą agregaty i bieżąca sesja.
- `preprocess_ops += sum(self.input_ops)` dodaje całą historię sesji przy każdym wywołaniu `answer_batch`. Dzisiejszy evaluator wywołuje tę metodę raz na sesję, ale ponowne użycie interfejsu naliczyłoby stary koszt ponownie.
- PC-01 używa współczynnika t około 4,30265 dla df=2, odpowiadającego dolnemu końcowi dwustronnego przedziału 95%. W REVIEW-01 nazwano go dolną jednostronną granicą 95%. To konserwatywna rozbieżność opisu; nie odwraca bardzo dużego dodatniego efektu.

## INTERPRETATION

### Czy projekt ma sens

Tak, jeśli jego jednostką postępu będzie konkretne, rozstrzygnięte pytanie o jakość i koszt. Na obecnym etapie wartością NEXTAI jest aparatura, historia falsyfikacji dokładnych implementacji oraz wiedza o ograniczeniach kilku mechanizmów. Nie ma podstaw, by przedstawiać repozytorium jako powstający już konkurent LLM.

Najważniejsza ogólna lekcja brzmi: ograniczenie pracy do małego fragmentu pamięci pomaga dopiero wtedy, gdy system potrafi poprawnie wybrać ten fragment, zinterpretować wejście i utrzymywać stan. Na małych generatorach poprawny adres lub reguła często są już wpisane w interfejs, więc hash-map, parser, RLS albo dokładny interpreter osiągają ten sam cel taniej. To użyteczna obserwacja badawcza, ale nie uniwersalne twierdzenie o niemożliwości uczenia.

Historia jest bardzo szeroka i płytka: 80 z 89 wersji ogólnych benchmarków ma jeden wynik. Część tej mnogości wynika z uzasadnionego oddzielania wersji, a nie z bezcelowego powielania. Mimo to ciągłe zmiany zadania, kontroli i kontraktu utrudniają budowanie długiej, porównywalnej linii dowodów. Kolejne 100 quicków nie daje automatycznie silniejszej odpowiedzi na główny cel.

Protokół v3 poprawił strategię, rozdzielając mechanizm, ekonomię i transfer. PC-01 zrealizował istotny brakujący element. MUC ponownie jednak pokazuje regresję jakości pomiarów względem standardu osiągniętego w PC-01. Nie można przenieść certyfikacji jednego zadania na nowe zadanie przez samą obecność tego samego frameworka lub biblioteki torch.

### Ocena kierunku pamięci i aktualizacji

Nowa pamięć z lokalną aktualizacją może być zasadnym tematem, ale przewaga musi być określona względem istniejących metod. Delta-rule w fast weights, wielokrokowe sieci pamięci i retrieval mają rozbudowane wcześniejsze odpowiedniki. Sprawdziłem ponownie źródła już zapisane w ledgerze: [fast weights i delta-rule](https://proceedings.mlr.press/v139/schlag21a.html), [End-To-End Memory Networks](https://arxiv.org/abs/1503.08895) oraz [RAG](https://arxiv.org/abs/2005.11401). Same składniki nie uzasadniają twierdzenia o nowości.

Moja inferencja: sensowny potencjalny wkład to wykazanie konkretnej przewagi w aktualizacji, retencji, routingu lub kosztach przy określonej jakości, z policzonym kosztem całego systemu. Obecny MUC nie pokazał takiej potrzeby: kontrola symboliczna rozwiązuje jego gramatykę dokładnie. Uczenie zgodności czterech nazw, a następnie wymaganie działania na większej przestrzeni identyfikatorów nie rozstrzyga głównego problemu pamięci.

Nie dodawałbym WT ani pushdown do nowego prototypu tylko dlatego, że miały wąskie dodatnie wyniki. Wymagania docelowego zadania powinny uzasadnić każdy komponent. Nie usunąłbym mocnej kontroli symbolicznej tylko po to, aby uczony model miał łatwiejszego przeciwnika.

### Co uprościć i zoptymalizować

| Zmiana | Uzasadnienie | Ograniczenie |
|---|---|---|
| Jedno źródło aktualnej kolejki | Zmniejsza sprzeczności między README, programem, LAB_PLAN i zagnieżdżonymi overlayami. | Zachować źródłowe zgody i historię; projekcja nie może tworzyć uprawnień. |
| Mniejsza aktywna ścieżka laboratorium | `command_plan_new` ma 613 linii, `laboratory_progress` 219, a schema planu 3284. Dodawanie nowej rodziny wymaga zmian w wielu miejscach. | Małe jawne adaptery kohort, bez budowania kolejnego ogólnego frameworka i bez przepisywania zamrożonych wersji. |
| Wspólne typy kosztu i kwalifikacji wyników | Dzisiaj nazwa `mean_query_ops` lub `p95` nie zapewnia wspólnej jednostki. To przyczyna faktycznych błędów. | Jednostka, licznik, mianownik i granica pomiaru powinny być jawne w nowym kontrakcie. |
| Zachowanie agregatów zamiast wszystkich sesji | Usuwa niepotrzebne utrzymywanie danych wielu światów i wielokrotne skanowanie historii kosztów. | Zachować potrzebne surowe pomiary jako artefakty, poza stanem roboczym modelu. |
| Rozdzielenie testów syntetycznych i integracyjnych | Chroni zakres danych i skraca pętlę lokalnych poprawek. | Pełna regresja musi być wybierana według uprawnień; sam marker `slow` nie wystarcza. |
| Cache parsowania i hashy w jednym wywołaniu audytu | Wspólne zależności 529 kandydatów są wielokrotnie analizowane. | Cache związany z treścią i jedną kontrolą; nie omijać kontroli zmienionych plików. |
| Widok aktywnych i historycznych modułów | Ułatwia pracę bez usuwania dowodów. | 446 krótkich plików kandydatów to często potrzebne role ablacyjne, a nie martwy kod. |

Dwa najwolniejsze testy nieaktywnej kohorty RID zajęły łącznie około 116,65 s, czyli 30,5% całej regresji. To konkretny punkt do rozdzielenia zestawów testów, nie argument za pomijaniem kontroli w końcowej autoryzowanej walidacji. Nie wykonywałem nowego benchmarku wydajności kodu ani nie obiecuję konkretnego przyspieszenia po refaktorze.

Nie zalecam masowego kasowania archiwów. 4398 plików archiwalnych zajmuje około 17,3 MB; oszczędność dysku byłaby mała, a koszt utraty pochodzenia duży. Zmniejszać należy złożoność aktywnej ścieżki i liczbę miejsc zmienianych przy nowym badaniu, nie liczbę zachowanych dowodów.

## CONFIDENCE

Wysoka pewność dotyczy liczności repozytorium, odtworzonych wartości wyników, rozbieżności raportu oraz błędów potwierdzonych małymi kontrolami. Wysoka jest również pewność, że PC-01 wykazał lokalny efekt uczenia i że WT ma klasycznie równoważne wyjaśnienie. Te wnioski opierają się na wynikach i kodzie, nie na nazwach hipotez.

Umiarkowana pewność dotyczy tego, jak bardzo poszczególne błędy danych treningowych przyczyniły się do 18,98% w MUC. Nie przeprowadzono kontrolowanego porównania naprawionej wersji; nie należy zgadywać rozmiaru poprawy. Niska jest pewność co do przyszłej przewagi architektonicznej. Obecne dane nie uzasadniają ani obietnicy przełomu, ani twierdzenia, że taki kierunek jest ogólnie niemożliwy.

Testy wykonano na istniejącym Windows i lokalnym środowisku. Nie wykonano natywnej reprodukcji Linux, nowego pomiaru energii, niezależnego zewnętrznego holdoutu ani przeglądu drugiego worktree NEXTAI-LAB-B. Lokalnie zapisane HEAD, origin/master i origin/main wskazywały ten sam commit; nie odpytywałem GitHub o bieżący stan zdalny.

## ALTERNATIVE EXPLANATIONS

Słaby wynik MUC może pochodzić z małego i stronniczego prefiksu treningowego, ograniczonej receptury, heurystyki wyboru najnowszego prawie najlepszego dopasowania, trudności z UNKNOWN lub połączenia tych przyczyn. Błąd jednostek kosztu nie zmienia sam z siebie odpowiedzi modelu, a błędna flaga kompozycji nie usuwa całej informacji z ogólnej accuracy. Dlatego diagnoza powinna pozostać rozdzielona na jakość, metryki i integralność.

Silne klasyczne rozwiązania są właściwymi punktami odniesienia, ale porażka drobnego uczonego estymatora na zadaniu rozwiązanym przez gotową regułę nie falsyfikuje całej rodziny. Również udane uczenie na jednym korpusie nie kalibruje automatycznie każdego następnego zadania. Nie przyjmuję zatem bezkrytycznie ani tezy „wszystkie stare negatywy są bezwartościowe”, ani „36 statusów falsified zamyka 36 wielkich kierunków AI”.

## DECISION

**KEEP**: zachować laboratorium, źródła i pełną historię, PC-01 jako dodatnią kontrolę, wąskie wyniki pushdown i opisowy efekt WT. **INCONCLUSIVE**: główna teza o lepszej architekturze oraz aktualna kalibracja uczonych kontroli MUC. **DISCARD**: używanie obecnych kosztów i p95 MUC do twierdzeń ekonomicznych oraz traktowanie liczby plików, cykli lub hipotez jako miary odległości od celu. **PROMOTE**: żadnej architektury.

Kolejność prac proponuję następującą:

1. Zablokować nieautoryzowany dostęp w testach i odczytach danych, poprawić STOP/PAUSE oraz własność blokady.
2. W nowej wersji evaluatora poprawić liczbę odpowiedzi, jednostki kosztu, granice komórek, surowe czasy i oznaczanie kompozycji. Uzgodnić raport z kontraktami wyników.
3. Przed nowym treningiem sprawdzić pokrycie danych, etykiety oraz rzeczywistą semantykę baseline'ów. Zachować negatywny wynik starej wersji.
4. Dopiero po kompetentnej kontroli wybrać jeden konkretny kontrast pamięci. Nie zaczynać kolejnej szerokiej populacji architektur.

To zalecenia do odrębnego, prospektywnego etapu naprawczego. Audyt nie zmienił manifestu ani nie odblokował scoringu. Bieżący stan pozostaje `MUC-01-CALIBRATION-DECISION`; licznik wyników 106 i cykli 299 nie został zwiększony.

## NEXT DISCRIMINATING EXPERIMENT

Nie uruchomiono ani nie prerejestrowano nowego eksperymentu. Najbliższą wykonalną pracą jest przeglądany pakiet napraw bez scoringu; jego warunki wyjścia powinny być konkretne: odrzucenie brakującej odpowiedzi, koszt niezależny od kolejności komórek, koszt na pytanie rosnący z rzeczywiście wykonanymi krokami, poprawny podział seen/unseen, brak sprzecznych par, egzekwowane STOP i zakres danych oraz brak przejmowania żywej blokady.

Następnym eksperymentem naukowym, tylko po nowej decyzji użytkownika, może być wersjonowana kalibracja kompetentnego baseline'u na MUC z oddzielonym skończonym dev i świeżymi światami finalnymi. Pytanie powinno brzmieć: „Czy faktycznie zaimplementowany, uczony od zera baseline osiąga zamrożone 0,85 ogólnej accuracy i 0,80 po zastąpieniu faktu przy poprawnym evaluatorze i zachowanym budżecie?”. To nadal test aparatury i kontroli; jeszcze nie test pamięci delta.

Konkretne receptury, liczba prób dev, zakres danych, nadzór zasobów i polityka zakończenia muszą znaleźć się w nowym kontrakcie przed implementacją testowanej zmiany. Pozytywny wynik takiej kalibracji może dopiero uzasadnić osobne porównanie delta-update z ablacją append-only przy identycznej reszcie systemu. Negatyw powinien prowadzić do decyzji o zadaniu lub recepturze, bez automatycznego powiększania budżetu i bez ratowania się starym holdoutem.
