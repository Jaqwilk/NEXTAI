# Przegląd literatury — cykl313, ukończone117

Przegląd wymagany po sześciu eksperymentach od poprzedniego licznika111.
Nie wykonano fitu, nowego EXP, danych, implementacji modelu lub promocji.
Nie zmieniono kadencji, metryk, progów ani ukończonego wyniku0002.
Nieudany końcowy doctor i jego105s kosztu pozostają zachowane.
Na przegląd konserwatywnie obciążono180s z bieżącego budżetu pomocniczego.
Sprawdzono pierwotne abstrakty i metadane publikacji; nie deklarujemy pełnego
przeglądu PDF. Źródła zapisane append-only w research/sources.jsonl.

## OBSERVATION — źródła

[Mikolov, Le i Sutskever2013](https://arxiv.org/abs/1309.4168) opisują uczenie
liniowej mapy między przestrzeniami wektorów słów z korespondencji bilingwalnych.
To bezpośredni wcześniejszy przykład wyuczonego transportu między widokami.
Nasza obserwacja w repozytorium: transport/PCA ma około99.94% pełnych odpowiedzi,
a kontrola bez uczenia około25%; ten wynik dotyczy świeżych sztucznych wektorów.

[DPR, Karpukhin i in.2020](https://aclanthology.org/2020.emnlp-main.550/)
opisuje uczone reprezentacje pytań i fragmentów tekstu w dwóch encoderach oraz
porównanie ze silną kontrolą BM25. Publikacja dotyczy retrievalu tekstowego;
nie jest dowodem transferu naszego zadania numerycznego, aktualizacji lub UNKNOWN.

[Johnson, Douze i Jégou2017](https://arxiv.org/abs/1702.08734) przedstawiają
zoptymalizowane wyszukiwanie podobieństwa: dokładne, przybliżone i skompresowane,
na GPU. Opublikowany opis uzasadnia traktowanie mocnych metod indeksowania jako
wiarygodnych alternatyw; wyników przepustowości tej pracy nie przenosimy na
latencję pojedynczego zapytania przy naszych małych K.

## INTERPRETATION — wnioski NEXTAI

Uczenie transportu, dopasowanie podpór i klasyczne indeksowanie mają wcześniejsze
odpowiedniki. Obecny wyuczony encoder z PCA nie jest nową architekturą.
PCA, ridge oraz aktualizacja według ostatniego znacznika czasu pozostają jawnie
klasycznymi elementami implementacji. Fit, parser, kopie, ingest, aktualizacje,
cache/indeks, zapytania i dekodowanie muszą być rozliczane.

0002 replikuje lokalny efekt uczenia; mocna kontrola ridge/PCA dominuje ekonomicznie
neuralny transport na deklarowanych osiach. Wybrana metoda klasyczna ma dodatnią
średnią różnicę jakości względem Transformera, lecz trzy przedziały przy szumie0.04
nie potwierdzają nieinferiorności2pp. To niepewność jednostek sparowanych, bez
prawa do osłabienia progu, ratunkowego tuningu lub promocji do świeżego finału.

## CONFIDENCE I NEXT DISCRIMINATING EXPERIMENT

Wysoka pewność ograniczonego efektu uczenia na tym jawnym zadaniu; brak podstaw
do nowości architektury, transferu lub ogólnej przewagi nad metodami klasycznymi.
Literatura nie naprawia niewystarczającego przedziału niepewności.

Następna prerejestracja: pięć świeżych par dla odporności klasyfikatora referencji,
stały model/4096 par/2048 kroków transportu/1024 decoder, ekspozycja zestawów
treningowych dense na szum0.02 versus ustalone mieszane0.02/0.04 jako jeden czynnik;
bez zmiany kalibracji, progów, mocnych kontroli, trzech skal i aktualizacji.
Najpierw kontrakt i walidacja klonu, potem jeden audytowany EXP w kolejnym cyklu.
Cel transferu na dwie rodziny i lokalnego prototypu pozostaje otwarty.
