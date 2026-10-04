# Rozdzielenie rankingu i braku odpowiedzi; nowy program NEXTAI

Cykl 304, 2026-10-04. Jest to analiza zapisanych wyników i przygotowanie
nowego programu, bez nowej rejestracji EXP, treningu badawczego ani inferencji.
Zakres zamrożono w `research/plans/NEXTAI-CONTINUATION-PREPARATION-V1.json`
przed implementacją skryptu i obsługi nowej autoryzacji. Analiza ma charakter
posthoc; nie zmienia metryk, progów ani decyzji zamkniętych eksperymentów.

## OBSERVATION

Źródłem jest niezmieniony EXP-20261004-0003, SHA256
`1e4731e5d0ad121a4c5fb34c9472a487eef25f288dea3d86b4b7bb8b747ca495`.
Pięć niezależnych jednostek obejmuje sparowany seed modelu i świeże dane.
Każda ma 135 światów rozwoju, 2160 pytań końcowych oraz 270 znanych i 270
nieznanych sond gęstego wyboru. Pytania z jednego świata nie stanowią
niezależnych replikacji. Poniższe liczby dotyczą sond gęstych, nie hybrydowego
wyniku końcowego z BM25.

| K | Top1, 768 → 8192 | UNKNOWN, 768 → 8192 | Nieznany podmiot, 8192 | Nieznana relacja, 8192 |
|---|---:|---:|---:|---:|
| 32 | 96,67% → 100,00% | 54,67% → 84,22% | 88,44% | 80,00% |
| 128 | 85,56% → 95,33% | 24,89% → 42,67% | 12,44% | 72,89% |
| 512 | 71,33% → 80,44% | 20,44% → 33,56% | 1,78% | 65,33% |

Liczba poprawnych sond nieznanego podmiotu przy K=512 wynosi 4/225.
Top1 po dłuższym treningu myli 109/1350 znanych sond; wszystkie te przypadki
wybierają błędny klucz. Żaden nie wybiera starszej wersji poprawnego klucza.
Znane fakty po 8192 krokach nie są odrzucane przy zamrożonym progu 0,5.
To rozdziela problem rankingu od nadmiernego odrzucania znanych faktów.

Odsetek fałszywie dodatnich ocen pojedynczych par dla nieznanych zapytań po
8192 krokach wynosi 0,722%, 0,599% i 0,433% odpowiednio przy K=32/128/512.
Maleje, chociaż odrzucanie całego zbioru gwałtownie się pogarsza. W świecie
jest odpowiednio 40/160/640 historycznych wierszy; wystarcza jedna dodatnia
ocena, żeby błędnie zaakceptować nieznane zapytanie. Nie przyjmujemy, że
oceny wierszy są niezależne, ani nie wyprowadzamy z tego prawa skalowania.

Wspólna receptura tworzy 2048 dodatnich i 2048 ujemnych par. Ujemne pary
łączą istniejące klucze z błędnymi dokumentami: połowa ma ten sam podmiot,
połowa tę samą relację. Nie obejmują nieobecnych podmiotów ani nieobecnych
relacji. Niezależna strata BCE dla par nie optymalizuje bezpośrednio decyzji
„żaden z K rekordów nie pasuje”. Jest to obserwacja kodu, a nie nowy test
causalny innej funkcji straty.

## INTERPRETATION

Wydłużenie treningu poprawiło rozróżnianie par i ranking. Przy dużym K
pozostają jednak dwa odrębne problemy: błędny zwycięzca dla znanego faktu
oraz akceptacja choć jednego rekordu dla nieznanego zapytania. Nie ma tu
dowodu, że sam dodatkowy fit naprawi kalibrację zbioru. Zaobserwowana różnica
między nieznanym podmiotem a nieznaną relacją uzasadnia osobne straty i
osobne metryki tych przypadków w ewentualnym nowym badaniu.

Listwise loss z jawnym NULL, trening nieobecnych zapytań i raportowanie
logitów są uzasadnionymi alternatywami dla dalszego zwiększania liczby
kroków. Nie zostały wykonane ani potwierdzone w tej analizie. Próg i reguła
remisów zamkniętego badania pozostają niezmienione. Zapisane wyniki nie
zawierają logitów: 23 remisy błędnych zwycięzców, w tym 20 z obiema
wartościami równymi 1, nie rozstrzygają nasycenia numerycznego. Nawet
hipotetyczne naprawienie wszystkich 23 dałoby najwyżej 93,63% top1, poniżej
zamrożonego progu 95%, i nie zmieniłoby decyzji UNKNOWN przy progu 0,5.

### Dlaczego MUC pozostaje testem technicznym

Poprawny algorytm można skonstruować bez nauczenia modelu:

1. Z publicznego zdania odczytaj czas, podmiot, relację i wartość.
2. Dla pary `(podmiot, relacja)` zapamiętaj wartość o największym czasie.
3. Odczytaj start i listę relacji z publicznego pytania.
4. Wykonaj kolejne odczyty mapy. Brak klucza daje UNKNOWN.

To dokładnie legalne obserwacje kontrolowanego systemu, bez dostępu do
prywatnego generatora lub odpowiedzi. Indukcja po długości ścieżki pokazuje,
że algorytm realizuje definicję odpowiedzi dla każdego poprawnego świata
MUC, także po aktualizacji. Publiczne nazwy ET/ED i pełna gramatyka nie
tworzą nieznanego problemu percepcyjnego. Kontrola symboliczna potwierdziła
100% na wszystkich 10800 pytaniach ostatniego badania.

MUC sprawdza parser, aktualizacje, składanie jawnych odczytów, prowadzenie
historii i rozliczenie. Nie wymaga uczenia i nie może sam potwierdzić, że
uczony mechanizm jest potrzebny do docelowej zdolności. Ulepszenie samej
neuralnej receptury nie usunęłoby tej silnej alternatywy. Zachowujemy MUC
oraz jego pełną kontrolę; nie osłabiamy jej, żeby uzyskać pozytywny wynik.

### Koszty i granice dotychczasowego porównania

W ostatnim badaniu fit obu ramion wyniósł 1066,874 s; wszystkie workery
łącznie 1906,701 s. Dopasowany zakres ingest + warmup + 10800 zapytań
wyniósł 41,042 s przy 768 krokach, 40,431 s przy 8192 i 0,177 s dla kontroli
symbolicznej. Czas aktualizacji jest częścią ingest; nie dodajemy go drugi
raz. P95 zapytań to odpowiednio 6670,7 / 6651,6 / 3,7 µs. Maksymalny
logiczny stan modelu wyniósł 43 292 428 B, kontroli 29 440 B. RSS procesu
kontroli obejmuje importy wspólnego harnessu i nie jest rozmiarem słownika.

Alokacji sesji nie zmierzono osobno, liczby FLOP są oszacowaniami, a gęste
sondy wykonano tylko dla modeli. Cały czas workera ma więc nierówny zakres.
Nie nazywamy tej tabeli pełnym certyfikatem ekonomicznym ani pomiarem
złożoności. Pokazuje ona silny lokalny punkt odniesienia, którego nie wolno
ominąć. Nowy kontrakt wymaga pomiaru alokacji, kopii danych i całego
dopasowanego obciążenia dla każdej metody.

## CONFIDENCE

Wzrost top1 768→8192 wynosi 7,407 pp, a pierwotny sparowany przedział 97,5%
wynosi [0,460; 14,355] pp, 5/5 par dodatnich. Wzrost UNKNOWN to 20,148 pp,
ale opisowy przedział 95% wynosi [−17,616; 57,912] pp: 3 pary dodatnie,
1 ujemna i 1 zerowa. Nie jest to pewny efekt naprawy braku odpowiedzi.
Przedziały wykorzystują pięć jednostek, nie tysiące zależnych zapytań.

Pewność w poprawność opisowego podziału i symbolicznego kontrprzykładu jest
wysoka. Pewność w postulowaną przyczynę kalibracyjną jest umiarkowana;
do jej potwierdzenia potrzebna byłaby świeża prerejestrowana interwencja
na danych lub stracie. Nie ma nowego dowodu przewagi architektury, kosztu
ani transferu do języka naturalnego.

## DECISION

KEEP MUC jako zamknięty test techniczny. DISCARD użycie tego benchmarku jako
jedynej podstawy dla twierdzenia o konieczności uczenia lub przewadze nowej
pamięci. Uczony mechanizm pozostaje INCONCLUSIVE; nowy program jest aktywny.
Jedna nieskuteczna receptura nie zamyka całego programu.

Rozpatrzono: naprawę listwise/NULL i nieobecnych przykładów w MUC; standardowe
symboliczne MQAR; nowe modelowanie języka; zadanie z rzeczywistą percepcją;
oraz pamięć na dwóch obserwacyjnych widokach tej samej nieznanej tożsamości.
Pierwsze dwie możliwości pozostawiają dokładny symboliczny solver. Nowe
modelowanie języka lub duża percepcja rozszerzyłyby rozmiar przygotowania
i utrudniły izolację kosztu dostępu do pamięci. Nie zostały sfalsyfikowane.
Wybieramy minimalne nowe zadanie PVM01 jako następny test przesiewowy,
z jawnym ograniczeniem do syntetycznej pamięci.

`research/plans/PVM01-TASK-CONTRACT-V1.json` zamraża nowe obserwacje i granice
przed implementacją. Zapis i pytanie mają różne zaszumione 64-wymiarowe
widoki nowej ciągłej tożsamości; pytanie nie ma klucza/handle, a losowa
wartość nie ujawnia widoku pytania. Zmiany używają jawnego handle zapisu,
dostępnego wszystkim kontrolom. Niezależne osie to K=32/128/512 oraz
0/1/4 rund aktualizacji; druga oś nie jest głębokością rozumowania.

Osobne prywatne parametry obserwacji, nie seed modelu, wyznaczą nowe widoki.
Trening dostarczy legalne pary odpowiadających sobie obserwacji. Brak
dokładnego klucza nie jest dowodem konieczności sieci neuronowej: trzeba
wykonać kontrolę zamrożoną, permutację etykiet i mocny klasyczny transport
ridge/kernel oraz retrieval z tym samym encoderem. Kontrole mają identyczne
surowe dane, a uczenie/preprocessing każdej z nich jest rozliczane.

Dotychczasowe bramki ekonomiczne zostają zachowane: porównywalna jakość,
co najmniej pięć niezależnych jednostek, jednoczesny dolny przedział różnicy
jakości ≥−2 pp, górny przedział ilorazu pełnego kosztu ≤0,8 i P95 ≤0,9,
brak dominacji mocnych metod klasycznych, ablacje, trudny wariant, trzy skale
i świeży finał po zamrożeniu źródła/receptury. Zadanie i nazwa modelu nie
zastępują dowodu kompetencji kontroli Transformer.

W literaturze MQAR jest narzędziem analizy pamięci, a learned metric matching
i aktualizacje delta mają wcześniejsze odpowiedniki:
[Zoology](https://arxiv.org/abs/2312.04927),
[Matching Networks](https://arxiv.org/abs/1606.04080),
[Fast Weight Programmers](https://arxiv.org/abs/2102.11174),
[Gated Delta Networks](https://arxiv.org/abs/2412.06464).
Są to przesłanki projektowe, nie dowód transferu naszego zadania ani nowości.
Pierwotne źródła zachowano jako SRC-0435 oraz SRC-0438..0440.

## INTEGRITY / BUDGET

Nowa autoryzacja i kontrakt programu zostały zamrożone w Git `a29c95e`.
Dotychczasowe 3 rejestracje i 2655,336485 s pozostają zużyte. Dalszy limit
to dokładnie 17 rejestracji i 69344 s; nie odzyskujemy zaokrąglonych 0,663515 s.
Obsługa kontynuacji sprawdza surowe hashe dokumentów, wyników i projekcję
zdarzeń starego programu oraz ponownie wylicza stare koszty. Stary program
pozostaje zamknięty. Koszt każdego testu, także nieudanego, obciąża nowy limit.
Ostateczne kwoty i wynik pełnej regresji zawiera oddzielny receipt tego cyklu.

Zachowano błąd nowego fixture'u brakującego schematu: 20 PASS / 1 FAIL,
5 s rozliczone. Po dołączeniu niezmienionych schematów 21 PASS, kolejne 5 s.
Nie powstał rzeczywisty plan EXP ani seed badawczy. Stare źródła, checkpointy,
wyniki, archiwa oraz historia pozostają niezmienione. WT 8–9 i dane finalne
nie były otwierane. Benchmark pozostaje w maintenance i scoring=false.

## NEXT DISCRIMINATING EXPERIMENT

Osobno prerejestrować PVM01-REFERENCE-V1: pięć sparowanych świeżych jednostek
train/dev, konwencjonalny dense Transformer i attention pointer, kontrole
zamrożona/permutowana oraz mocny transport klasyczny. Zamrozić konkretne
modele, straty, skończone siatki i capy przed implementacją generatora/modelu.
Wykonać jeden EXP przez audytowany runner dopiero po testach w klonie,
freeze/preflight i receipt gotowości. Warunek wejścia do mechanizmu: kompetencja
i wpływ legalnego uczenia na świeżych tożsamościach. Przy porażce ocenić
oddzielną prerejestrowaną alternatywę, bez retry i bez zamknięcia programu
tylko za jedną recepturę. Finał pozostaje niewykonany do freeze całej receptury.

Reprodukcja diagnozy, bez inferencji:

```powershell
uv run --no-sync python scripts/analyze_muc_ranking_absence.py --root C:/Users/NATAN/Documents/ChatGPT/NEXTAI-VALIDATION-20261002 --experiment EXP-20261004-0003
```

Pełne liczniki: `research/reviews/NEXTAI-MUC-RANKING-ABSENCE-V1.json`.
Niepewność: `research/reviews/NEXTAI-MUC-RANKING-ABSENCE-UNCERTAINTY-V1.json`.
