# Przegląd portfela — cykl 303, wyniki 99–110

Wymagany przegląd po 12 nowych zakończonych wpisach jest wykonany na zachowanych
wynikach. Nie ma nowego scoringu, fitu badawczego, hipotezy, literatury ani seeda.
Przegląd obejmuje także awarię, negatywy i niewygodne seedy. Poprzedni przegląd
obejmował 98 wpisów; obecny stan ma 110. Liczniki ukończeń, stare budżety,
HYP-0012 i BELIEFS pozostają bez zmian. Przegląd literatury nie jest jeszcze
należny: 5 nowych wyników od stanu 105 przy kadencji 6.

## OBSERVATION

| Wynik | Obserwacja | Ograniczenie i decyzja |
|---|---|---|
| EXP-20260902-0001 | SuiteSparse: wszystkie solvery zbieżne; obcy prolongator poprawiał residual o około 1e−10, poniżej progów. Koszt R16 731,6 mln operacji wobec 63,6 mln silnych klasycznych kontroli. | DISCARD dokładny feature map/ridge/Jacobi; brak dowodu obcej struktury, jeden seed, rodziny i rozmiary współzmienne. |
| EXP-20260905-0001 | PC-01 dev: WinError 5 podczas atomowego zapisu device.json; utrwalony checkpoint 750, spadek loss istnieje, wynik niekompletny. | Awaria aparatury; INCONCLUSIVE, nie falsyfikacja transformera. Zachowana konserwatywna opłata 1200 s i brak ukrycia próby. |
| EXP-20260905-0002 | PC-01 dev2: 5000 kroków, wszystkie kontrole; wybrany krok 1500 daje 2,191943 bpb, wobec frozen 8,128573 i unigram 4,756899. Późny loss pogarsza się do 2,589923. | Kompetentny lokalny kontrolny efekt uczenia; jeden korpus i jeden dev seed, bez przewagi ekonomicznej. |
| EXP-20260905-0003 | PC-01 final1: 2,480891 bpb, frozen 8,040791; świeża inicjalizacja, poprawne 10 kontroli i metadata GPU. | Pierwsza z trzech zamrożonych replik, bez final-guided rescue. |
| EXP-20260905-0004 | PC-01 final2: 2,484464 bpb, frozen 8,118559; poprawna tożsamość i kontrole. | Druga replika na tym samym korpusie, nie drugi korpus. |
| EXP-20260905-0005 | PC-01 final3: 2,514378 bpb, frozen 8,042679. Cała seria przechodzi własne bramki. | KEEP positive_control_pass; średni kontrast 5,574099 bpb, dolna jednostronna granica t 95% 5,439192. Nie promocja architektury, transfer ani ekonomia. |
| EXP-20260906-0001 | WT: 162 poprawne próby, kontrast recurrence NRMSE 0,162794 wobec progu 0,033433; VAR(2)/ARX zgadza się do 3,55e−15. | Wąski efekt klasycznej rekurencji, 2 zapisy fizyczne i 1 permutacja; brak nowości lub fizycznej replikacji. WT 8–9 pozostają zamknięte; w tym przeglądzie czytano tylko zapisane wyniki. |
| EXP-20260906-0002 | MUC v1: dense 18,98%, BM25 75,51%, klasyczna mapa 100%; pary train około 86,6%. | Referent niekompetentny. Błędna historyczna normalizacja operacji uniemożliwia wniosek ekonomiczny; pamięci delta nie zbadano. |
| EXP-20261002-0001 | Audyt MUC v2: dense 23,66%, uczone BM25 48,84%, frozen BM25 15,14%, klasyczna mapa 100%. | Aparatura i rachunek kosztów poprawione; lokalny efekt uczenia w jednym seedzie, nadal brak kompetentnego referenta. |
| EXP-20261004-0001 | 5 par random/hard przy 192 krokach: top1 10,96→23,11%, UNKNOWN 10,00→23,41%; oba skorygowane CI obejmują zero. Jeden hard seed odrzuca 94,44% znanych sond. | DISCARD dokładną recepturę jako gotową poprawę; ogólna użyteczność hard pozostaje nierozstrzygnięta. Nie usuwamy załamania. |
| EXP-20261004-0002 | 5 par hard 192/768: train 77,32→95,75%, top1 22,74→70,15%; oba główne CI wykluczają zero, 5/5 dodatnich par. UNKNOWN po 768 tylko 23,63%. | KEEP niedouczenie 192 jako lokalną diagnozę; DISCARD 768 jako stabilny referent. Namespace gap 2,96 pp nie przechodzi zamrożonej bramki 10 pp. |
| EXP-20261004-0003 | 5 świeżych par 768/8192: train 98,54→99,87%, top1 84,52→91,93%; główne CI wykluczają zero. Dense UNKNOWN 53,48%, jeden seed top1 80%, E2E 96,07%; klasyczna mapa 100%. | Trzecia receptura nadal nie przechodzi stałych bramek top1/UNKNOWN. INCONCLUSIVE porównanie mechanizmu, bez czwartej receptury, bez nowej architektury. |

Hashowane źródła tego przeglądu znajdują się w towarzyszącym pliku JSON.
Seria PC-01 jest uwierzytelniona w research/analyses/PC-01-FINAL-SERIES-V1.md;
jej oryginalne 2394,270825 s / 7200 s pozostają rozliczone oddzielnie.

## INTERPRETATION

Mamy teraz odtwarzalny dodatni kontrolny efekt uczenia PC-01 i lokalny efekt
rekurencji WT, który wyjaśnia równie dobry model klasyczny. To realny postęp
pomiaru. Nie znaleźliśmy przewagi mechanizmu NEXTAI nad silną klasyczną kontrolą.
MUC ujawnił trzy oddzielne rzeczy: krótkie 192 kroki są niedouczone, dalsze
uczenie poprawia ranking, a rozpoznawanie nieobecnych kluczy pozostaje słabe
mimo niemal idealnego train. Wyższa jakość całego czytnika korzysta również
z publicznego parsera, BM25 i jawnej pętli, których pracy nie przypisujemy sieci.

Długi MUC nie zawodzi przede wszystkim przez zmianę namespace T→D: IID i D
mają zbliżony top1. To ograniczony negatyw dla konkretnej zamrożonej diagnozy,
nie dowód pełnej generalizacji. K=512 obniża top1 do 80,44%; duża liczba
konkurujących rekordów i absent-subject są nadal ważnymi lukami. Diagnostyka
remisów prawdopodobieństw jest post hoc; nawet idealna korekta wszystkich
23 zaobserwowanych remisów nie podniosłaby top1 do wymaganych 95%.

Front Pareto z EXP-0003 wymaga sond dense, niezmierzonych dla klasycznej mapy.
Dlatego nie może zaświadczać przewagi wobec tej kontroli. Nie zmieniamy osi
ani starego wyniku. Osobny opisowy audit wspólnych osi E2E pokazuje, że mapa
klasyczna dominuje wszystkie odczytane agregaty jakości/query-time/stanu/fitu.
Nie jest to certyfikat pełnego kosztu: new_session nie ma osobnego timera,
worker zawiera różne dodatkowe sondy, a operacje GPU są estymatami.

## CONFIDENCE

Wysoka pewność dotyczy kompletności i parowania dwóch najnowszych badań oraz
nieprzejścia jawnych bramek. Efekt długości treningu jest lokalnie powtórzony;
metoda paired t używa 5 jednostek seed/dane, nie tysięcy niezależnych pytań.
Przedziały zależą od założeń metody i mają słabo weryfikowalną normalność przy
n=5. Rozrzut UNKNOWN jest duży i opisowy CI jego zmiany obejmuje zero.
Nie przenosimy pewności PC-01 na MUC ani syntetycznej publicznej gramatyki na LLM.

## ALTERNATIVE EXPLANATIONS

Pozostają: rozbieżność loss par treningowych z rankingiem po wielu rekordach,
kalibracja obecności klucza, przypadkowe skróty relacji/podmiotu, nasycenie
float32 i ograniczony kontrakt danych. Nie rozstrzygnięto ich odrębną ablacją.
Niski koszt dokładnej mapy jest też konsekwencją jawnego i zamkniętego języka;
nie dowodzi łatwości naturalnego języka. Awaria PC i stare invalidacje są
historią aparatury, nie negatywnymi wynikami rodzin architektonicznych.

## DECISION

KEEP odtwarzalną aparaturę, dodatni kontrolny efekt PC-01 i diagnozę niedouczenia.
DISCARD testowane receptury MUC jako stabilny referent. Zgodnie z zamrożonym
limitem trzech receptur zamknąć autonomiczny program jako INCONCLUSIVE po
weryfikacji końcowej: brak kompetentnego referenta blokuje wejście do testu
mechanizmu. Budżet globalny nie został wyczerpany; limit nie wymusza jego
spalenia ani czwartej receptury. BELIEFS i niepowiązane hipotezy nie są zmieniane.

## NEXT DISCRIMINATING EXPERIMENT

Żaden kolejny eksperyment w zamykanym programie. Niewykonane pozostają wybór
mechanizmu delta-memory, source-identical ablacje, skalowanie przy dopasowanej
jakości, adverse generalization i świeży final. Ewentualny nowy kontrakt musi
najpierw rozdzielić ranking wielu kluczy od kalibracji absent-subject; nie może
używać tych dev jako final ani po wyniku zmieniać progów. To opis potrzebnego
dowodu, bez nowego planu wykonania, seeda, implementacji czy zgody na retry.
