from pathlib import Path
import json,subprocess
from nextai_autoresearch.ledger import read_jsonl,append_jsonl
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.report import write_report
b=Path.cwd();now=utc_now();review='research/reviews/PVM01-LITERATURE-CYCLE-313-V1.md'
assert not (b/review).exists()
entries=[
 {'title':'Exploiting Similarities among Languages for Machine Translation','url':'https://arxiv.org/abs/1309.4168','authors':['Tomas Mikolov','Quoc V. Le','Ilya Sutskever'],'year':2013,'claims_supported':['The paper learns a linear mapping between distributed word-vector spaces from bilingual correspondences.'],'relevance':'NEXTAI inference: fitted cross-view transport followed by matching has direct prior art; our linear toy-task result is not a new retrieval architecture or language transfer.'},
 {'title':'Dense Passage Retrieval for Open-Domain Question Answering','url':'https://aclanthology.org/2020.emnlp-main.550/','authors':['Vladimir Karpukhin','Barlas Oguz','Sewon Min','Patrick Lewis','Ledell Wu','Sergey Edunov','Danqi Chen','Wen-tau Yih'],'year':2020,'claims_supported':['The work learns dense question/passage embeddings in a dual-encoder framework and compares retrieval against a strong BM25 control.'],'relevance':'NEXTAI inference: keep strong classical alternatives. PVM01 vectors and UNKNOWN/update laws do not establish passage-retrieval or text transfer; separate ranking from abstention.'},
 {'title':'Billion-scale similarity search with GPUs','url':'https://arxiv.org/abs/1702.08734','authors':['Jeff Johnson','Matthijs Douze','Herve Jegou'],'year':2017,'claims_supported':['The paper presents optimized brute-force, approximate and compressed-domain similarity search on GPUs and releases its implementation for comparison.'],'relevance':'NEXTAI inference: exact/classical indexing is credible systems prior art. GPU throughput claims do not predict our single-query latency; charge cache/index allocation, builds, updates and all service operations.'}]
last=max(int(s['source_id'].split('-')[1]) for s in read_jsonl(b/'research/sources.jsonl'))
for i,entry in enumerate(entries,1):
    entry.update(source_id=f'SRC-{last+i:04d}',checked_at=now,source_type='paper',primary_source=True,checked_scope='Primary paper abstract and publisher/arXiv bibliographic page, not claimed full-PDF review')
    append_jsonl(b/'research/sources.jsonl',entry)
text="""# Przegląd literatury — cykl313, ukończone117

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
"""
(b/review).write_text(text,encoding='utf-8',newline='\n')
state_path=b/'research/state.json';state=json.loads(state_path.read_text())
assert state['completed_experiments']==117 and state['last_literature_review_completed_experiments']==111
state['last_literature_review_completed_experiments']=117;state['updated_at']=now;atomic_write_json(state_path,state)
append_jsonl(b/'research/events.jsonl',{'event':'literature_review_completed','created_at':now,'cycle':313,'completed_experiments':117,'review_path':review,'review_sha256':sha256_file(b/review),'source_ids':[e['source_id'] for e in entries],'new_research_fit_or_scoring':False,'hypothesis_confidence_unchanged':True,'cadence_unchanged':True,'auxiliary_seconds_charged':180})
write_report(b)
print('Required bounded literature review completed; cadence pointer117, all research outcomes unchanged',flush=True)
