# Ocena naukowa pomysłu

## Werdykt

Pomysł **ma sens jako długoterminowy, wysokiego ryzyka program badań**, jeżeli jego bezpośrednim celem jest odkrywanie i falsyfikowanie zasad obliczeniowych, a nie obietnica szybkiego „zastąpienia LLM”. Najsilniejsza część manifestu to nacisk na prawa skalowania, wiele małych zakładów, pełne baseline’y, rozdzielenie obserwacji od interpretacji i gotowość porzucenia ACC/SCCS.

Pomysł **nie ma jeszcze sensu jako pojedyncza hipoteza architektoniczna**. ACC/SCCS jest nazwą szerokiej intuicji, nie kompletnym modelem: nie definiuje reprezentacji, reguły uczenia, mechanizmu routingu, kryterium zbieżności ani kosztu uzyskania odpowiedzi. Tych braków nie należy uzupełniać wielkim buildem. Każdy z nich staje się osobnym pytaniem eksperymentalnym.

Najuczciwsze obecne prawdopodobieństwa jakościowe są następujące:

- wysoka wiarygodność, że w zadaniach strukturalnych można oddzielić pojemność pamięci od aktywnego kosztu prostego zapytania;
- średnia wiarygodność, że hybrydy małego kontrolera, pamięci i wyspecjalizowanych operatorów dadzą istotne korzyści w ograniczonych domenach;
- niska, lecz niezerowa wiarygodność, że jedna z tych rodzin zachowa przewagę po przejściu do otwartego języka i szerokich zadań;
- brak obecnych dowodów, że taki system zastąpi frontier LLM albo da poprawę rzędu 10–100× przy porównywalnej inteligencji.

To wystarcza, aby prowadzić badania. Nie wystarcza, aby deklarować kierunek zwycięski.

## Co w tezie jest dobrze postawione

### 1. Rozdzielenie wiedzy i aktywnego obliczenia jest testowalne

Nie należy wymagać, aby każda informacja w systemie brała udział w każdym zapytaniu. Bazy danych, pamięci asocjacyjne, retrievery, grafy i sparse MoE pokazują ograniczone wersje tej własności. Istotnym pytaniem jest nie „czy da się coś pobrać lokalnie”, lecz czy **nauczony, otwarty system** potrafi znaleźć właściwy fragment i reasoning bez ukrywania kosztu w routingu.

### 2. Prawa skalowania są ważniejsze niż wynik małego benchmarku

Program słusznie rozdziela:

- `K`: całkowitą wiedzę;
- `D`: trudność/reasoning depth;
- `C`: koszt końca-do-końca.

Pożądana sygnatura to mała pochodna kosztu po nieistotnej wiedzy przy zachowanej jakości:

```text
d log(C) / d log(K) ≈ 0
```

oraz koszt rosnący przede wszystkim z niezbędną pracą rozumowania. Harness estymuje oba nachylenia osobno. Nachylenie bliskie zeru na toy tasku jest tylko dowodem poprawności mechanizmu, nie ogólnej inteligencji.

### 3. Małe testy falsyfikujące są właściwym początkiem

Wielki prototyp mieszałby reprezentację, pamięć, uczenie, routing i dekoder. Nie wiadomo byłoby, co zadziałało. Mikroworld umożliwia kontrolę K, D, rozkładu danych, zakłóceń i prawdziwej odpowiedzi.

### 4. ACC/SCCS nie jest uprzywilejowane

To konieczne. Lokalne reakcje mają atrakcyjne własności, ale mogą:

- wykonywać w praktyce pełny sweep stanu;
- przenieść koszt do ogromnej liczby kroków;
- mieć trudny problem credit assignment;
- wpadać w chaotyczne lub martwe dynamiki;
- wymagać ręcznie zdefiniowanej ontologii;
- powtarzać NCA, graph rewriting, production systems albo message passing pod nową nazwą.

ACC pozostaje w portfelu z niskim priorem i tanim testem zabijającym.

## Najważniejsze poprawki do manifestu

### 1. „Capability / cost” nie może być jednym skalarem

Capability jest wektorem, a koszt również:

```text
Q = [accuracy, OOD, composition, planning, update retention, ...]
C = [FLOPs, ops, bytes moved, latency, RAM, energy, update cost, ...]
```

Wczesne wyniki należy porównywać frontem Pareto. Jeden scalar score można wprowadzić dopiero po jawnej decyzji o wagach dla określonego zastosowania.

### 2. Trzeba zdefiniować granicę systemu

Do kosztu inferencji wchodzą:

- parsowanie wejścia i tworzenie reprezentacji;
- routing/retrieval oraz odczyt indeksu;
- aktywne moduły i iteracje;
- cache miss i cache warm-up;
- dekoder/język wyjściowy;
- komunikacja CPU–GPU i pamięć;
- amortyzowana konserwacja indeksu, jeśli aktualizacje są częścią zastosowania.

Koszt Codexa prowadzącego badania jest raportowany osobno jako koszt R&D. Nie wchodzi do kosztu inferencji kandydata, ale nie może być ukryty w demonstracji działania kandydata.

### 3. Wymagana jest prerejestracja

Autonomiczny agent może nieświadomie dopasowywać hipotezę po wyniku. Dlatego plan, przewidywanie, baseline’y, kryteria porażki i polityka interpretacji są haszowane **przed** uruchomieniem.

### 4. Widoczny benchmark nie jest ślepym holdoutem

Codex widzi pliki repozytorium. Może więc optymalizować implementację do widocznego harnessu. Lokalny wynik służy do screeningu zasad. Mocne twierdzenie wymaga osobnego ewaluatora, tajnego/odizolowanego zbioru lub późniejszej niezależnej replikacji.

### 5. Porażka implementacji nie falsyfikuje rodziny

`crash`, zła optymalizacja lub źle dobrana reprezentacja obniżają zaufanie do implementacji. Rodzinę falsyfikuje dopiero eksperyment rozróżniający jej kluczowe przewidywanie od alternatyw.

### 6. Należy chronić przed fałszywą nowością

Najbliższe poprzedniki obejmują retrieval-augmented models, sparse MoE, adaptive computation, NTM/DNC, program induction/DreamCoder, neural cellular automata oraz HDC/VSA. Promocja hipotezy wymaga precyzyjnej odpowiedzi:

```text
co już istnieje?
co tutaj jest inne?
jaki test mierzy właśnie tę różnicę?
```

### 7. „Działa cały czas” musi oznaczać serię ograniczonych cykli

Proces bez limitu jest trudny do audytu, może nakładać uruchomienia i zużywać zasoby bez informacji. Wariant natywny dla Codexa wykonuje dokładnie jeden ograniczony cykl na zaplanowane wznowienie i zachowuje cały stan w repozytorium.

## Kryteria minimalnego „następcy LLM”

Kandydat może być nazywany co najwyżej „zalążkiem alternatywnej zasady”, dopóki nie spełni kolejnych bram:

1. **Mechanizm:** pokazuje kontrolowaną sygnaturę, np. koszt niezależny od K.
2. **Uczenie:** nie otrzymuje gotowego rozwiązania/ontologii i uczy się użytecznej struktury.
3. **Kompozycja:** rozwiązuje niewidziane kombinacje, nie tylko interpoluje.
4. **Transfer:** zasada działa w więcej niż jednej rodzinie zadań.
5. **Continual learning:** lokalne aktualizacje nie niszczą starej wiedzy.
6. **Język bez dużego nauczyciela w pętli:** naturalne wejście/wyjście nie wymaga frontier LLM przy każdym zapytaniu.
7. **Matched capability:** przewaga kosztowa utrzymuje się przy porównywalnej jakości.
8. **Skalowanie:** przewaga rośnie lub przynajmniej nie znika wraz ze skalą.
9. **Replikacja:** wynik przechodzi ślepy lub niezależny test.

Dopiero bramy 7–9 uzasadniają rozmowę o następcy LLM.

## Realność na obecnym komputerze

Wykryty sprzęt to RTX 4070 12 GB oraz i7-13700K. Zainstalowany PyTorch jest obecnie buildem CPU, więc Generation 0 korzysta z lekkich testów CPU i dokładnych liczników operacji. To wystarcza do:

- mikroworldów;
- algorytmów grafowych i program synthesis w małej skali;
- HDC/VSA;
- małych układów recurrent/NCA;
- tysięcy krótkich testów jednostkowych i screeningowych.

Nie wystarcza do uczciwej konkurencji z frontier LLM. Po wyłonieniu zasad należy skonfigurować kontrolowany stos CUDA i mały Transformer baseline dopasowany do 12 GB VRAM. Ta inwestycja ma nastąpić po Generation 0, nie przed nią.

## Pierwszy eksperyment kontrolny

`successor_graph_v1` nie szuka AGI. Sprawdza, czy infrastruktura wykrywa znane różnice:

- `linear_scan`: koszt rośnie z K;
- `indexed_graph`: koszt zależy głównie od D;
- `memoized_graph`: powtórzone zapytania są tańsze, lecz aktualizacja unieważnia cache;
- `compiled_jump`: reasoning depth może zostać skompilowany kosztem pamięci i aktualizacji;
- `dense_recurrent`: dokładna, ale pełna macierz powoduje koszt zależny od K²;
- `random_guess`: kontrola ujemna.

Jeżeli harness nie odzyska tych jakościowych praw, nie nadaje się jeszcze do poszukiwania nieznanych praw.

## Decyzja

Należy kontynuować, ale pod następującą nazwą operacyjną:

> **program odkrywania i falsyfikowania alternatywnych zasad obliczeniowych**

Nie:

> projekt, który już buduje następcę LLM.

Ta różnica chroni przed narracją wyprzedzającą dowody, nie zmniejszając ambicji celu końcowego.

