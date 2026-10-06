# Przegląd literatury — cykl329, 123 ukończone eksperymenty

Prerejestracja: NEXTAI-LITERATURE-CYCLE329-V4, commit fe49209. Zakres obejmuje
wyłącznie abstrakty i metadane trzech ustalonych publikacji pierwotnych, odczytane
2026-10-06 po zamrożeniu planu. Nie deklarujemy analizy pełnych PDF ani odtworzenia
ich wyników. Zero nowych danych, fitu, EXP lub architektur. Kadencja6 pozostaje.
Trzy błędy ścieżek podczas autorstwa prerejestracji, ich źródła i częściowe kopie
metadanych są zachowane; cały czas od02:53:30Z podlega limitowi1200s.

## OBSERVATION

[Robinson, Chuang, Sra i Jegelka, 2020/ICLR2021](https://arxiv.org/abs/2010.04592)
opisują kontrolowane próbkowanie trudnych negatywów w nienadzorowanym uczeniu
kontrastywnym. Abstrakt raportuje poprawę reprezentacji w kilku modalnościach.
Nie stanowi to dowodu poprawy odmowy odpowiedzi, kosztów naszego pipeline ani
skuteczności nadzorowanego samplera zastosowanego w MUC.

[Geifman i El-Yaniv, 2017](https://arxiv.org/abs/1705.08500) opisują selektywną
klasyfikację: odrzucanie części predykcji w celu kontroli ryzyka kosztem pokrycia.
Ich deklarowane gwarancje dotyczą własnej procedury i założeń; nie przenosimy
ich na progi MUC, nowe rozkłady, transfer ani ten eksperyment.

[Rajpurkar, Jia i Liang, 2018](https://aclanthology.org/P18-2124/) przedstawiają
SQuADRUn, łączący pytania z odpowiedzią z pytaniami bez odpowiedzi, napisanymi
tak, aby przypominały odpowiadalne. Zadanie wymaga rozpoznania, czy kontekst
popiera odpowiedź. To przykład potrzeby osobnego pomiaru braku odpowiedzi;
nie oceniliśmy NEXTAI na tym zbiorze i nie pobraliśmy go.

Sześć zachowanych wyników po poprzednim przeglądzie117 to
EXP-20261005-0003/0004/0005/0006/0007 i EXP-20261006-0001. A wykazało lokalną
adekwatność stałej receptury wobec nieaugmentowanej referencji i silną klasyczną
alternatywę, po zachowanym negatywnym potwierdzeniu0004. Nie dowiedziono przewagi
augmentacji ani pełnej ekonomicznej kwalifikacji neuronowej. HAR0007 miał100%
nominalnego rankingu, ale zawiódł bramki informacji ze źródła i odmowy; jego
referencja dense nie była kompetentna, więc porównanie ekonomiczne jest
INCONCLUSIVE. To różne pytania i kohorty, bez wspólnego estymatora.

MUC0001: ranking9.333%→17.333%, różnica+8pp, sparowany97.5%CI
[-3.869,+19.869]pp. Dense UNKNOWN30%→15.852%, różnica-14.148pp,
97.5%CI[-55.633,+27.336]pp. Znane fałszywe odmowy0%→9.481%, co przekracza
zamrożoną średnią bramkę+2pp. Decyzja discard_proposed_recipe pozostaje.
Wynik E2E UNKNOWN+21.630pp jest odrębnym endpointem z BM25 top4 i szerokim
95%CI[-4.556,+47.815]pp; nie zastępuje nieudanego endpointu primary dense.

## INTERPRETATION

Wniosek NEXTAI: wyższy ranking podobieństwa może współistnieć z gorszym
rozpoznawaniem braku faktu oraz większą odmową przy obecnej odpowiedzi.
Literatura uzasadnia oddzielne osie oceny i mocne kontrole, lecz nie naprawia
nieudanych zamrożonych bramek. Dobór trudnych negatywów ma znane precedensy;
MUC nie dowodzi nowej architektury, transferu językowego lub przewagi ekonomicznej.
Zachowujemy pełne koszty parsera, tworzenia danych, fitu, kalibracji, ingest,
aktualizacji, cache, zapytań i dekodowania.

## CONFIDENCE

Wysoka pewność audytowanej decyzji dla dokładnej receptury MUC i zachowania
historycznych wyników. Niska pewność wielkości efektu w populacji przy pięciu
parach i szerokich przedziałach; nieudana kwalifikacja nie dowodzi braku każdego
możliwego efektu trudnych negatywów. Przegląd abstraktów daje ograniczony kontekst
metodologiczny. Pełny cel transferu i prototypu nadal pozostaje aktywny.

## ALTERNATIVE EXPLANATIONS

Wrażliwość kalibracji, skład negatywów, typ braku relacji wobec braku podmiotu
i wariancja świeżych światów to hipotezy, nie ustalone przyczyny. Pierwsza para
ma30% fałszywych odmów, a zysk rankingu maleje przy większymK; opis ten nie daje
prawa do usuwania par, zmiany progu, ratunkowego tuningu ani ponownego fitu.
HAR ma dodatkowo problem kompetencji referencji. ASM ma problem serializacji,
który nie jest naukowym nullem uczenia lub transferu.

## DECISION

Zachować wszystkie wyniki, błędy i koszty. Odrzucić dokładną recepturę MUC zgodnie
z prerejestracją. Nie zmieniać modeli, progów, źródeł naukowych ani kadencji.
Zamknąć prawdziwy przegląd dopiero po zapisaniu trzech zgodnych rekordów źródeł,
następnie wykonać jedną nową sekwencję utrzymania w niezależnym klonie. To osobny
zakres bez scoringu, a nie powtórzenie naukowego lub końcowego testu etapu MUC.
Rezerwa B7rejestracji/47000s pozostaje chroniona. Przegląd nie oznacza gotowości
do scoringu; ASM nadal wymaga nowego, konkretnego kontraktu.

## NEXT DISCRIMINATING EXPERIMENT

Najbliższe przygotowanie powinno osobno zamrozić dokładną gramatykę normalizera
ASM traktującego X/Y jako nieprzetwarzane tokeny, emitowane markery, obsługę pustych
stroke, granice rozmiaru i skończoną macierz syntetycznych przypadków. Bez native,
tablic, geometrii, fitu lub EXP. Histograma nie wolno uznać za dowód monotoniczności
seriali ani tego, że podpisaneY są literalnym-0. Późniejszy oddzielny intake musi
wykazać zgodność74 dawnych tablic oraz wszystkich1830 próbek bez filtrowania,
zanim nowa prerejestracja naukowa dopuści porównanie transferu. Ten tekst nie
upoważnia implementacji, intake, kolejnej architektury ani kolejnego EXP.
