from pathlib import Path
import json
from nextai_autoresearch.utils import sha256_file, utc_now, atomic_write_json
from nextai_autoresearch.ledger import append_jsonl

b=Path.cwd(); identity='EXP-20261004-0006'
a=json.loads((b/f'research/reviews/{identity}-PVM01-delta-analysis.json').read_text(encoding='utf8'))
d=json.loads((b/f'research/reviews/{identity}-PVM01-full-diagnostics-V2.json').read_text(encoding='utf8'))
r=json.loads((b/f'research/results/{identity}.json').read_text(encoding='utf8'))
labels={'dense':'Dense CUDA','dense_cached_cpu':'Dense cache CPU','dense_cached_cuda':'Dense cache CUDA','pointer':'Pointer CUDA','exact_nn_cpu':'Learned exact NN CPU','delta':'Learned transport + delta RFF','additive':'Learned transport + additive RFF','delta_untrained':'Delta untrained','delta_shuffled':'Delta shuffled','ridge':'Ridge float64 scan','ridge32':'Ridge float32 scan','ridge_pca_scan':'Ridge PCA scan','ridge_pca_tree':'Ridge PCA exact tree','kernel':'Nyström scan','raw':'Raw cosine'}
order=['dense','dense_cached_cpu','dense_cached_cuda','pointer','exact_nn_cpu','delta','additive','ridge','ridge32','ridge_pca_scan','ridge_pca_tree','kernel','delta_untrained','delta_shuffled','raw']
quality=['| Metoda | Full % | Updated % | Retained % | UNKNOWN % | False abstention % |','|---|---:|---:|---:|---:|---:|']
cost=['| Metoda | Fit faza s | Pełna seria s | p95 µs | Stan KiB | Peak RSS MiB |','|---|---:|---:|---:|---:|---:|']
for arm in order:
    x=d['summary'][arm]
    quality.append('| '+labels[arm]+' | '+' | '.join(f'{100*x[m]["mean"]:.4f}' for m in ('accuracy','updated','retained','dense_unknown_rejection','known_false_abstention'))+' |')
    cost.append(f'| {labels[arm]} | {x["fit_phase_seconds"]["mean"]:.4f} | {x["full_workload_seconds"]["mean"]:.6f} | {x["p95_query_us"]["mean"]:.2f} | {x["logical_state_bytes"]["mean"]/1024:.2f} | {x["peak_rss_bytes"]["mean"]/1024**2:.1f} |')
primary=['| Kontrast | Średnia pp | Jednoczesny 98,75% CI pp | Dodatnie jednostki |','|---|---:|---:|---:|']
for key in ('updated','retained','untrained','shuffled'):
    x=a['primary_simultaneous_intervals'][key]
    primary.append(f'| {key}: delta minus kontrola | {100*x["mean"]:.4f} | [{100*x["low"]:.4f}, {100*x["high"]:.4f}] | {x["positive_units"]}/5 |')
text=f'''# {identity} — delta poprawia aktualizację; silne kontrole nadal dominują ekonomicznie

Decyzja: **KEEP narrow delta mechanism for further validation**. Wszystkie
prerejestrowane bramki pierwotne i kompetencji przeszły. Cel całego programu
pozostaje otwarty; nie wykazano przewagi nad mocnymi kontrolami klasycznymi.

## OBSERVATION

Niezmienny plan: research/plans/{identity}.json; kanoniczny SHA-256
{r['plan_sha256']}. Prospektywny kontrakt:
research/plans/PVM01-DELTA-MEMORY-SCREEN-V1.json, raw SHA-256
{a['study_sha256']}. Prerejestracja przed implementacją:
6555a6ac87e74a9ab34ebce00d3af416e9a35fd8. Wykonane źródło:
399d7eceaa4e56f7ba96072107625f7700f27289. Surowy wynik:
research/results/{identity}.json, raw SHA-256 {a['result_sha256']}.

Jedno audytowane uruchomienie w niezależnym klonie, od {r['started_at']} do
{r['completed_at']}. **75/75 workerów,675/675 prób, pięć świeżych sparowanych
jednostek seed/dane**,216000 odpowiedzi15 metod. Metoda/jednostka ma45 epizodów,
2880 pytań i14280 zapisów/aktualizacji. K32/128/512 oraz aktualizacje0/1/4;
historyczne etykiety reasoning_depth1/2/3 nie oznaczają rozumowania. Pytania,
epizody i workery nie zwiększają liczby niezależnych replik.

Generator i kontrakt legalnych obserwacji nie zmieniły się. Pięć nowych seedów
oraz niezależnych nonce256bit jest rozłącznych z zużytymi0004/0005. Wszystkie
15 metod otrzymały identyczne legalne tablice T/D na jednostkę, potwierdzone
hashami. Kalibracja wyłącznie na27 epizodach T obejmuje wszystkie K i aktualizacje;
siatka, reguła wyboru, metryki i bramki były zamrożone. Nie wykorzystano dawnych
tablic, checkpointów lub kalibracji. Nowa kohorta v3 nie jest podstawą do
przyczynowego porównania jakości z wcześniejszym v2 lub MUC.

Transport neuralny: ten sam64→64 residual MLP,4096 par,2048 AdamW steps.
Dense: dwa bloki width64/heads4/FF256 oraz1024 set-loss steps. Delta/additive:
identyczne encodery, inicjalizacje, pełne alignment losses i RFF2048/sigma0,35.
Jedyna różnica tej pary to odjęcie bieżącej predykcji podczas zapisu. Beta=1
jest stała. W jest zerowane na epizod, dict timestampów wyłącznie odrzuca
starsze zapisy. Nie ma uczenia kontrolera, treningu przez pamięć ani ukrytego
indeksu wartości/kluczy.

Średnie pięciu jednostek, równa waga komórek; updated/retained dla rund1/4:

{chr(10).join(quality)}

{chr(10).join(primary)}

Kontrole: updated/retained versus additive; full versus untrained/shuffled.
Cztery dwustronne przedziały Student-t df4 o poziomie98,75% dają Bonferroni
rodzinowe95% przy założeniach modelu przedziałów. Updated spełnia średnią>=10pp,
dolny koniec>=5pp i5/5 dodatnich par. Retained spełnia dolny koniec>=−2pp;
przedział obejmuje zero, więc nie potwierdza dodatniego efektu retencji.
Oba gainy uczenia spełniają średnią>=20pp i dolny koniec>=10pp.
Wszystkie bramki kompetencji delta/dense przeszły.

Delta full99,7986%, opisowy95% CI[99,6543,99,9429]%; UNKNOWN99,5278%,
nieobcięty t-CI[98,9481,100,1075]%. Przy K32/128/512 full100/100/99,3958%,
UNKNOWN100/100/98,5833%. K512 false abstention0,3333% średnio, przy mniejszych
K zero. Surowe wyniki wszystkich jednostek i komórek pozostają zachowane.

Pamięć RFF nie zwraca uchwytu faktu: fact_top1/wrong_fact/stale-at-correct-handle
są NULL z applicable=false. Updated100% dotyczy wartości odpowiedzi i nie
dowodzi wskazania dokładnego rekordu przy kolizji wartości. Metody retrieval
z wyuczonym transportem mają known fact top1=100%. Wysoki UNKNOWN kontroli
untrained/shuffled wynika z niemal stałej odmowy także dla znanych pytań.

Pełny koszt załadowanej usługi obejmuje alokację, kopie, encoding, RFF/W, ingest,
indeks, aktualizacje, cache, warm-up, pytania, dekodowanie, synchronizację i
Python output. Aktualizacje są podzbiorem ingest i nie są doliczane ponownie.
Fit i inicjalizacja procesu są oddzielnie ujawnione oraz rozliczone. p95
jest percentylem wszystkich2880 raw query samples workera, następnie średnią
pięciu takich percentyli, a nie średnią p95 komórek.

{chr(10).join(cost)}

Fit faza/generacja/kalibracja223,5436153s; wewnętrzny fit algorytmów160,0469090s.
**Całe workery449,7621115s /11100s**. Kontroler i rejestracja498,2781735s;
overhead poza workerami48,5160620s obciążono jako49s. Wszystkie udane i nieudane
testy mają append-only rozliczenie. Finalny koszt etapu i programu:
research/laboratory/PVM01-CYCLE-308-COMPLETION-V1.receipt.json.

Opisowy sparowany stosunek delta/dense-cache-CPU: pełny koszt0,573162,
95% CI[0,558382,0,587942]; p95 ratio0,259304 CI[0,243715,0,274893].
Różnica full accuracy−0,2014pp CI[−0,3457,−0,0571]pp.
To screening przy jednej stałej kolejności i jednym komputerze, bez crossoveru
czasowego, trudnego wariantu i świeżego finału; nie formalny wynik ekonomiczny.
Ridge64 około9,38x szybszy, PCA scan7,78x szybszy i6,93x mniejszy stan niż delta,
z100% jakości. Learned exactNN CPU jest2,68x szybszy i ma mniejszy stan przy
tym samym encoderze. cKDTree exact eps0 ma rozliczone kopie float64 i rebuild.
Logiczny stan nie jest całkowitym RSS. Nie wybrano jedynie wolnego wariantu CUDA.

Integralność przed/po1111/1111, evaluator {r['evaluator_sha256']},
bundle {r['integrity_before']['candidate_bundle_sha256']}.
Siedem wyuczonych ramion ma identyczne encodery; scan/tree identyczne wagi,
projekcję i wybór PCA. Cache ma identyczny kod, seed i dane; wszystkie2880
zapisane odpowiedzi/top_value/handle każdej jednostki zgadzają się z dense.
Maksymalna różnica score2,98023224e−7, set-loss8,94069672e−8.
Nie zebrano hasha końcowych wag dekodera i nie twierdzimy bitowej identyczności
tych wag. Prerejestrowany test cache na wspólnych niezerowych wagach przeszedł.

Przed seedem końcowa pełna regresja1096/1096, zero pominięć, doctor/preflight/
readiness PASS. Źródło i runtime zachowano przed maintenance;1728 raw plików
archiwów oraz4 native diagnostics sprawdzono w indeksie Git przez SHA256.
Oryginalne15759 plików głównego repo pozostawały bez zmian przed integracją.
Historyczne CRLF archiwów zachowano. Nieudany whitespace-check i nieudany
pierwszy raw diagnostic check zachowano; pierwszy obciążono pełnym180s capem.
Nieudane kontrole pre-seed i opcjonalnej wizualizacji także zachowano/rozliczono.

Eksploracyjna diagnostyka V1 błędnie potraktowała brak decoder-hash jako false.
V2 ujawnia brak pomiaru i rzeczywiste różnice. Nie zmienia to pierwotnych bramek.
Błędny opis p95 w0005 poprawiono osobnym dodatkiem bez zmiany tamtego wyniku,
liczb lub decyzji. Pełne dane jednostek/komórek i korekty:
research/reviews/{identity}-PVM01-delta-analysis.json oraz
research/reviews/{identity}-PVM01-full-diagnostics-V2.json.

## INTERPRETATION

Przy tym samym nauczeniu transportu i cechach lokalna reguła delta ma duży
przyczynowy efekt aktualizacji nad additive. Kontrole uczenia wykazują potrzebę
poprawnej mapy obserwacji dla tej hybrydy; nie dowodzą uczenia reguły pamięci.
Uczony encoder z klasyczną korektą i stałą beta pozostaje hybrydą.

[Schlag, Irie, Schmidhuber2021](https://arxiv.org/abs/2102.11174) opisali
wcześniejszą delta fast-weight rule, a [Rahimi i Recht2007](https://proceedings.neurips.cc/paper/2007/hash/013a006f03dbc5392effeb8f18fda755-Abstract.html)
random Fourier features. To minimalny test, nie wierna reprodukcja ani nowość.
Kontrola indeksu jest oparta na [SciPy cKDTree](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.html).
Pomimo poprawy względem dense, mocne klasyczne i wyuczone explicit retrieval
wykonują zadanie taniej z lepszą jakością. Ta receptura nie realizuje pełnego celu.

## CONFIDENCE

Wysoka pewność lokalnego efektu przy pięciu dodatnich jednostkach, wspólnym
source/data/fit i kompetentnej kontroli. T-CI przy n5 mają ograniczenia
dystrybucyjne. Jakość/koszty na innym sprzęcie, przy innym query/update ratio,
większej pojemności i innych widokach są nieznane. Ekonomiczna przewaga nad
silnymi kontrolami nie ma poparcia. Nie zmieniono HYP-0012 ani BELIEFS.json.

## ALTERNATIVE EXPLANATIONS

Znane własności LMS/kernel memory mogą wyjaśniać efekt bez nowej zasady.
Niemal liniowa mapa zadania pozwala ridge/PCA działać bardzo dobrze.
Koszt małych wywołań CUDA batch1 nie jest teorią złożoności. Trafna wartość
nie zawsze wskazuje tożsamość faktu przy kolizjach. Uczony transport,
wyuczone cechy, stała reguła i faktycznie uczony kontroler to odrębne pytania.

## DECISION

**KEEP narrow delta mechanism for further validation**. Nie promować
architektury ani twierdzić przewagi ekonomicznej. Zachować dokładną recepturę
i jej koszt jako wynik; bez tuning rescue na obecnym D. Current study terminalne,
benchmark maintenance/scoring=false. Program NEXTAI-CONTINUATION pozostaje
aktywny. Stare koszty i rejestracje pozostają zużyte. Bez retry, WT8–9,
zewnętrznych modeli/API i zmian harmonogramu.

## NEXT DISCRIMINATING EXPERIMENT

Następny ograniczony cykl ma prerejestrować test uczenia kompaktowej mapy cech
przez lokalną pamięć: wyuczona mapa versus identyczna zamrożona mapa i
permutowane korespondencje przy stałej mniejszej pojemności. Pięć nowych
sparowanych jednostek, K32/128/512, aktualizacje0/1/4; zachować dense z cache
CPU/CUDA, ridge fp32, PCA scan/tree, Nyström i learned indexed/exact retrieval.
Model, pojemność, trening na T-epizodach, kalibracja, koszty, bramki i capy
muszą być zamrożone przed kodem. Nowe pytanie o reprezentację/koszt/pojemność,
bez retry lub zwiększania kroków obecnej receptury. Nie zaimplementowano
alternatywy i nie widziano jej danych. Jeżeli brak uzasadnionej receptury,
wykonać ograniczony przegląd alternatyw zamiast wymuszać dodatni wynik.

Trzy lokalne skale i obecne ablacje nie zastępują trudnego wariantu, replikacji
i zamrożonego świeżego finału. Cały cel pozostaje niezrealizowany.
W tym cyklu nie uruchomić drugiego EXP.
'''
path=b/f'research/analyses/{identity}.md'; assert not path.exists()
path.write_text(text,encoding='utf8',newline='\n')
header=f'''# Current cycle308 — {identity} completed (2026-10-04)

One delta-memory screen:75/75 workers,675/675 trials, five fresh paired units.
Updated additive→delta39.83→100%; gain60.17pp simultaneous98.75% CI[56.90,63.43],
5/5positive. Retained contrast+0.61pp CI[−0.76,1.99] passes−2pp; both learning
contrasts≈74.82pp and all delta/dense competence gates pass.
KEEP narrow delta mechanism; no novelty, learned controller, economic/transfer
claim or architecture promotion. Delta full99.7986%, UNKNOWN99.5278%;
dense/cache and strong fitted retrieval/classics100%.
Full service delta0.8302s versus cacheCPU1.4487s and ridge0.0885s;
PCA scan0.1067s and68.25KiB versus delta473KiB. Full objective remains open.
Fit phase223.5436s, full charged workers449.7621s; all failed/valid auxiliary
checks charged append-only. Plan/result/source/runtime preserved before maintenance.
Analysis:research/analyses/{identity}.md. MUC and0004/0005 results unchanged.
Current study terminal, maintenance/scoring=false, continuation active.
3/17 new tickets used; old3 tickets/2655.336485s carried unchanged. No retry,
WT8–9, external models/API or schedule change. Use uv run nextai lab status.
Next bounded cycle: preregister compact learned-feature memory versus frozen
and shuffled controls, optimized dense and strongest classical/retrieval
controls; or finite evidence-based alternative review. No new implementation,
seed/data before freeze. Adverse, scaling, replication and frozen fresh final
remain required. No second EXP in this completed cycle.
Previous sections are preserved historical states.

'''
for f in ('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','docs/SCIENTIFIC_PROTOCOL.md'):
    q=b/f; q.write_text(header+q.read_text(encoding='utf8'),encoding='utf8',newline='\n')
q=b/'config/research.toml'; content=q.read_text(encoding='utf8')
assert content.count('status = "active"')==1
q.write_text(content.replace('status = "active"','status = "maintenance"',1),encoding='utf8',newline='\n')
append_jsonl(b/'research/events.jsonl',{'event':'research_program_study_analyzed','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1','experiment_id':identity,'analysis_path':path.relative_to(b).as_posix(),'analysis_sha256':sha256_file(path),'decision':a['decision'],'whole_program_complete':False,'retry_authorized':False})
atomic_write_json(b/'research/reviews/PVM01-DELTA-ANALYSIS-LIMITATIONS-ADDENDUM-V1.json',{'id':'PVM01-DELTA-ANALYSIS-LIMITATIONS-ADDENDUM-V1','created_at':utc_now(),'primary_and_competence_gates_unchanged':True,'optional_plot_omitted':'matplotlib unavailable in project and bundled artifact runtime; failed checks preserved and charged; no dependency installed','cache_limitation':'No direct decoder hash; V2 discloses actual tiny set-loss and score differences, all observed answer/handle values identical','old_latency_label_corrected_append_only':True,'paid_run_repeated':False})
print(json.dumps({'analysis_path':str(path),'analysis_sha256':sha256_file(path),'decision':a['decision'],'status':'maintenance','whole_goal_complete':False}))

