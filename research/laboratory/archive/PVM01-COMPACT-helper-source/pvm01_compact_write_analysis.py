"""Write the immutable report from frozen primary analysis and stored diagnostics."""
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from nextai_autoresearch.utils import sha256_file

b = Path.cwd()
identity = "EXP-20261004-0007"
a = json.loads((b / f"research/reviews/{identity}-PVM01-compact-analysis.json").read_text())
d = json.loads((b / f"research/reviews/{identity}-PVM01-full-diagnostics-V2.json").read_text())
assert a["decision"] == "DISCARD exact RFF512/512-step learned feature recipe"
assert a["result_sha256"] == d["result_sha256"] == sha256_file(b / f"research/results/{identity}.json")
for name in ("PVM01-COMPACT-preseed-full-V1", "PVM01-COMPACT-postrun-full-V1"):
    receipt = json.loads((b / f"research/reviews/{name}.json").read_text())
    suites = list(ET.parse(b / f"research/reviews/{name}.xml").getroot().iter("testsuite"))
    assert sum(int(s.attrib["tests"]) for s in suites) == 1108
    if name.endswith("preseed-full-V1"):
        assert receipt["returncode"] == 0
        assert all(sum(int(s.attrib.get(k, 0)) for k in ("failures", "errors", "skipped")) == 0 for s in suites)
    else:
        assert receipt["returncode"] == 1
        assert sum(int(s.attrib.get("failures", 0)) for s in suites) == 1
        assert all(int(s.attrib.get("errors", 0)) == int(s.attrib.get("skipped", 0)) == 0 for s in suites)
        failures = [(case.attrib["name"], case.find("failure")) for suite in suites for case in suite.iter("testcase") if case.find("failure") is not None]
        assert len(failures) == 1 and failures[0][0] == "test_checked_in_research_lifecycle_is_consistent"
        assert "result lacks required analysis: EXP-20261004-0007" in (failures[0][1].text or "")
order = ("compact_learned", "compact_frozen", "compact_shuffled", "compact_additive", "delta", "dense",
         "dense_cached_cpu", "dense_cached_cuda", "exact_nn_cpu", "ridge", "ridge32", "ridge_pca_scan", "ridge_pca_tree", "kernel", "raw")
labels = {"compact_learned":"Learned features512 + delta", "compact_frozen":"Frozen features512 + delta",
          "compact_shuffled":"Shuffled features512 + delta", "compact_additive":"Learned features512 + additive",
          "delta":"Learned transport + RFF2048 delta", "dense":"Dense CUDA", "dense_cached_cpu":"Dense cache CPU",
          "dense_cached_cuda":"Dense cache CUDA", "exact_nn_cpu":"Learned exact NN CPU", "ridge":"Ridge float64",
          "ridge32":"Ridge float32", "ridge_pca_scan":"Ridge PCA scan", "ridge_pca_tree":"Ridge PCA exact tree",
          "kernel":"Nyström scan", "raw":"Raw cosine"}
def mean_metric(arm, key):
    return d["descriptive_95_percent_intervals"][arm][key]["mean"]
quality = ["| Metoda | Full % | Updated % | Retained % | UNKNOWN % | Known false abstention % |",
           "|---|---:|---:|---:|---:|---:|"]
costs = ["| Metoda | Fit faza s | Pełna seria s | p95 µs | Stan KiB | Peak RSS MiB |",
         "|---|---:|---:|---:|---:|---:|---:|"]
cuda = ["| Metoda | Peak allocated MiB, średnia | Peak reserved MiB, średnia | Zakres reserved MiB |",
        "|---|---:|---:|---:|"]
for arm in order:
    quality.append("| " + labels[arm] + " | " + " | ".join(f"{100*mean_metric(arm, key):.4f}" for key in
                   ("accuracy", "updated", "retained", "dense_unknown_rejection", "known_false_abstention")) + " |")
    row = d["descriptive_95_percent_intervals"][arm]["costs"]
    costs.append(f"| {labels[arm]} | {row['fit_phase_seconds']['mean']:.4f} | {row['full_workload_seconds']['mean']:.6f} | "
                 f"{row['p95_query_us']['mean']:.2f} | {row['logical_state_bytes']['mean']/1024:.2f} | {row['peak_rss_bytes']['mean']/1024**2:.1f} |")
    units = [d["whole_worker_cuda_allocator_peaks"][f"pvm01_{arm}_s{i}"] for i in range(5)]
    alloc = [u["allocated_bytes"]/1024**2 for u in units]
    reserve = [u["reserved_bytes"]/1024**2 for u in units]
    cuda.append(f"| {labels[arm]} | {sum(alloc)/5:.3f} | {sum(reserve)/5:.3f} | {min(reserve):.3f}–{max(reserve):.3f} |")
contrasts = ["| Kontrast | Średnia pp | Jednoczesny 98,75% CI pp | Dodatnie jednostki |",
             "|---|---:|---:|---:|"]
for key, label in (("frozen", "Full: learned minus frozen"), ("shuffled", "Full: learned minus shuffled"),
                   ("K512_updated", "K512 updated: learned minus frozen"), ("retained", "Retained: learned512 minus RFF2048")):
    v = a["primary_simultaneous_intervals"][key]
    contrasts.append(f"| {label} | {v['mean']*100:.4f} | [{v['low']*100:.4f}, {v['high']*100:.4f}] | {v['positive_units']}/5 |")
Ktable = ["| Metoda | K32 full / UNKNOWN % | K128 full / UNKNOWN % | K512 full / UNKNOWN % |", "|---|---:|---:|---:|"]
for arm in ("compact_learned", "compact_frozen", "compact_shuffled", "delta", "dense_cached_cpu", "ridge_pca_scan"):
    row = d["descriptive_95_percent_intervals"][arm]["by_K"]
    Ktable.append("| " + labels[arm] + " | " + " | ".join(f"{row[str(k)]['accuracy']['mean']*100:.4f} / {row[str(k)]['dense_unknown_rejection']['mean']*100:.4f}" for k in (32,128,512)) + " |")
cache = [v for u in d["cache_checks"].values() for v in u.values()]
assert all(v["predictions_handles_values_equal"] and v["count"] == 2880 for v in cache)
assert all(all(v[key] for key in ("initial_parameters_sha256", "final_encoder_sha256", "alignment_losses", "PCA_scan_tree_common_fit"))
           for v in d["identity_checks"].values())
cache_score = max(v["max_decision_score_absolute_difference"] for v in cache)
cache_loss = max(v["max_set_loss_absolute_difference"] for v in cache)
learned = d["descriptive_95_percent_intervals"]["compact_learned"]
accuracy, unknown = learned["accuracy"], learned["dense_unknown_rejection"]
pc = d["descriptive_paired_comparisons"]["dense_cached_cpu"]
ratio = pc["full_workload_seconds_ratio"]
feature = [v for key,v in d["feature_training_traces"].items() if key.startswith("compact_learned/")]
source = subprocess.check_output(["git","rev-parse","3338c78"],text=True).strip()
text = f"""# {identity} — uczenie mapy512 nie naprawia utraty retencji

Decyzja: **{a['decision']}**. Porównanie jest ważne technicznie;
wszystkie cztery kryteria pierwotne oraz kompetencja uczonej pamięci zawodzą.
Cel całego programu pozostaje otwarty. Wynik nie falsyfikuje rodziny architektur.

## OBSERVATION

Niezmienny plan: research/plans/{identity}.json; kanoniczny SHA-256
{a['plan_sha256']}. Prospektywny kontrakt:
research/plans/PVM01-COMPACT-FEATURE-SCREEN-V1.json, raw SHA-256
{a['study_sha256']}. Prerejestracja z zachowanymi raw bytes przed implementacją:
2ba76b6c9b2d4de1d76dcbcca7b3e4de5663c48a; wykonane źródło:
{source}. Raw wynik SHA-256:
{a['result_sha256']}.

Jedno audytowane uruchomienie w niezależnym Git klonie od {d['started_at']}
do {d['completed_at']}. **75/75 workerów,675/675 prób, pięć świeżych sparowanych
jednostek seed/dane**,216000 odpowiedzi15 metod. Metoda/jednostka ma45 epizodów,
2880 pytań i14280 zapisów/aktualizacji. K32/128/512 oraz aktualizacje0/1/4;
historyczne etykiety reasoning_depth1/2/3 nie oznaczają rozumowania.
Niezależne n=5; pytania, epizody, komórki i workery nie są dodatkowymi replikami.

Generator i legalne obserwacje pozostały bez zmian. Pięć nowych seedów oraz
nonce256bit jest rozłącznych z zużytymi0004/0005/0006. Wszystkie15 metod
otrzymały identyczne tablice T/D. Dense i compact miały identyczne legalne
T-sets. Żadnych dawnych checkpointów, tablic lub kalibracji nie użyto.
Nowa kohorta v4 nie uprawnia do przyczynowych porównań jakości między
eksperymentami v2/v3/v4 lub z MUC. Wewnątrz v4 pary są kontrolowane.

Wszystkie cztery ramiona compact używają identycznego poprawnego transportu
64→64 residual MLP,4096 par/2048 steps, wyjściowej mapy Fourier512/sigma0,35,
precompute i init. Encoder jest zamrożony podczas uczenia częstotliwości.
Learned i additive mają identyczny fit,512 strat, gradientów i losowań;
zmienia się tylko odjęcie bieżącej predykcji przy zapisie. Frozen nie zmienia
mapy, shuffled permutuje query-episode dla feature-loss przy poprawnym
transporcie/supportach/etykietach i tych samych losowaniach batch/value.
Beta=1, W512×16 zerowane na epizod; timestamp dict wyłącznie odrzuca stare
zapisy. Brak wyuczonej bramki, kontrolera, replay lub ukrytego indeksu kluczy.
Feature-fit:512 AdamW steps,lr0,003,clip1;17-class CE przez wszystkie zapisy
na128 legalnych T-epizodach K32/128, batch4,6 known/2 NULL queries i nowo
losowanych wartościach. Kalibracja27 T-epizodów obejmuje K32/128/512 i wszystkie
aktualizacje. Siatka progów i wybór wyłącznie na T były zamrożone.

Średnie pięciu jednostek z równą wagą komórek; updated/retained dla rund1/4:

{chr(10).join(quality)}

{chr(10).join(contrasts)}

Cztery dwustronne Student-t df4,98,75%, dają Bonferroni rodzinowe95% przy
założeniach modelu przedziałów. Full versus frozen/shuffled i K512 updated
wymagały średniej≥5pp, dolnego końca≥2pp i5/5 dodatnich par. Retained versus
RFF2048 wymagał dolnego końca≥−2pp. Wszystkie cztery kryteria zawodzą.
5/5 małych dodatnich różnic versus shuffled nie zastępuje przedziału ani
zamrożonej wielkości efektu. Przedział obejmuje zero. Dla K512 updated
frozen już jest blisko sufitu; wymagany gain5pp nie jest osiągnięty i bramki
nie zmieniono po wyniku. Minus1e−16 w jednej parze jest szumem arytmetycznym.

Compact nie spełnia mean full≥95%, mean UNKNOWN≥95%, each-unit UNKNOWN≥90%,
each-K full≥90% i known false-abstention≤2%; wszystkie each-unit full≥90%
przechodzą. Dense oraz oba cache przechodzą wszystkie bramki kompetencji.
Learned full90,7778%, opisowy95% CI[{100*accuracy['low']:.4f},{100*accuracy['high']:.4f}]%;
UNKNOWN92,0833%, opisowy95% CI[{100*unknown['low']:.4f},{100*unknown['high']:.4f}]%.

{chr(10).join(Ktable)}

Pamięć compact/delta zwraca wartości, bez uchwytu faktu. Fact_top1/wrong_fact/
stale-at-correct-handle są NULL z applicable=false. Updated99,2222% nie
dowodzi wskazania dokładnego rekordu przy kolizji wartości. Raw ma prawie
stałą odmowę znanych pytań; wysoki UNKNOWN nie oznacza kompetencji.

Pełny koszt załadowanej usługi obejmuje alokację, kopie, encoding, RFF/W,
ingest, indeks, aktualizacje, cache, warm-up, pytania, dekodowanie, synchronizację
i Python output. Aktualizacje są podzbiorem ingest i nie są doliczane ponownie.
Generacja tablic, kalibracja, fit i inicjalizacja procesu są ujawnione osobno
i całe workery rozliczone. p95 powstaje ze wszystkich2880 surowych próbek
query workera, następnie średniej pięciu percentyli; nie ze średniej p95 komórek.

{chr(10).join(costs)}

Fit faza/generacja/kalibracja{d['total_supervised_fit_phase_seconds']:.7f}s;
wewnętrzny fit algorytmów{d['total_internal_algorithm_fit_seconds']:.7f}s.
**Całe workery{d['full_charged_worker_seconds']:.7f}s /15600s**.
Kontroler i rejestracja664,5983516s; overhead poza workerami70,0753177s
obciążono konserwatywnie76s. Testy udane/nieudane i końcowe rozliczenie:
research/laboratory/PVM01-CYCLE-309-COMPLETION-V1.receipt.json.
Cap pomocniczy1800s i pierwotny deadline23:32:56Z obejmują wszystkie kontrole;
nie zresetowano wcześniejszych kosztów, attemptów lub deadline.

Opisowy sparowany compact/cacheCPU full-cost ratio{ratio['mean']:.6f},
95% CI[{ratio['low']:.6f},{ratio['high']:.6f}]. Utrata full accuracy
−9,2153pp CI[−9,7812,−8,6494]pp. Zatem mniejszy koszt nie dotyczy dopasowanej
jakości. Ridge jest około5,38× szybszy, PCA scan4,34× szybszy i2,71× mniejszy
logicznie, z full99,9861%. Learned exactNN także jest szybszy i dokładniejszy.
Nie wybrano jedynie wolnego CUDA dense. Jedna maszyna i stała kolejność
workerów, bez temporalnego crossoveru, trudnego wariantu lub świeżego finału;
to opisowe koszty screeningu, bez ekonomicznej promocji lub prawa skalowania.
Operation counts są oszacowaniami. Stan logiczny nie jest całym RSS.

Szczyty alokatora CUDA z całego workera, obejmujące fit i ewaluację:

{chr(10).join(cuda)}

Nie izolowano rezerwacji GPU podczas samej inferencji CPU. PyTorch allocator
nie obejmuje całego sterownika/kontekstu lub innych procesów. Energia nie
była mierzona. Nie twierdzimy, że usługa wcześniej trenująca na GPU ma przy
inferencji CPU zerowy koszt GPU. Wszystkie75 dzienników/hashe są zachowane.

Integralność przed/po1136/1136; evaluator
28e84508b8dbd6bf3520be80ed1392ecc02a4a46c89889e0b942eb5e69f10629;
bundle ceb0430f4c46b5b0f4da407a85cea32af0ac5cf91afb96663232f7781672a9e2.
Wszystkie dziewięć wyuczonych ramion ma identyczny encoder/initial/alignment;
PCA scan/tree identyczne fitted weights,projekcję,siatkę i wybór.
Dense/cache mają zgodne wszystkie2880 odpowiedzi/top_value/handle na jednostkę;
max score difference{cache_score:.9g}, set-loss{cache_loss:.9g}.
Nie zebrano hasha końcowych wag dekodera; nie twierdzimy o bitowej identyczności.
Test równoważności cache na wspólnych niezerowych wagach przeszedł przed seedem.

W klonie pełna regresja1108/1108 przed seedem, zero errors/failures/skips;
doctor/preflight/readiness PASS przed paid run. Po powrocie do maintenance
pełna regresja1107/1108, zero errors/skips; jedyny failure to wymagany
brak jeszcze niezapisanej analizy. To błąd kolejności zamknięcia, nie modelu.
Po zapisaniu niniejszego raportu kontrola lifecycle/report oraz doctor/lab
są ponawiane; końcowy dowód i koszt są w completion receipt. Pozostałych
1107 przypadków nie powtarza się bez nowej zmiany źródła lub awarii.
1142 pliki źródła i607 runtime zachowano przed maintenance; wszystkie raw
hashes oraz native stdout/stderr sprawdzono przy trwałym stagingu Git.
Stan przed integracją17615 plików oryginału i append-only prefixes jest
osobno weryfikowany; wyniki, analizy, archiwa i historyczne budżety pozostają.
Końcowe receipts stanowią źródło stanu integracji/publikacji i rozliczenia.

Zachowane porażki pomocnicze: postrun lifecycle wymagał analizy przed testami,
a pierwszą kontrolę doctor uruchomiono także przed jej zapisem. Raport
naprawia ten brak bez zmiany gates, kodu badawczego lub wyników.
Pre-seed history-guard V1 błędnie odczytał
integrity[files] zamiast checked_files; V2 naprawił tylko helper i przeszedł.
Mały read-only printer miał NameError po poprawnej analizie pierwotnej;
jego dodatkowy1s charge odnotowano jawnie po błędzie. Diagnostyka V1 użyła
nieistniejących nazw pól PCA i podała false; V2 porównuje rzeczywiste zapisane
fp32_ridge_weights_sha256/pca_projection_sha256 i potwierdza zgodność.
Wszystkie V1 i koszty zachowano. Żaden z tych błędów nie zmienił modelu,
danych, pierwotnych gates lub ukończonego wyniku; nie było retry modelu.
Szczegóły: research/reviews/{identity}-PVM01-compact-analysis.json oraz
research/reviews/{identity}-PVM01-full-diagnostics-V2.json.

## INTERPRETATION

Przy tej konkretnej recepturze uczenie mapy512 na K32/128 nie naprawia
interferencji/retencji przy K512. Częstotliwości zmieniły się, gradienty są
niezerowe, wszystkie512 kroki wykonano. Średnia CE pierwszych50 kroków
{min(v['first50_mean'] for v in feature):.6f}–{max(v['first50_mean'] for v in feature):.6f},
ostatnich50 {min(v['last50_mean'] for v in feature):.6f}–{max(v['last50_mean'] for v in feature):.6f}.
Strata na małych supportach już była niska; jej spadek nie przyniósł
prerejestrowanego efektu D. To nie dowód globalnej optymalności lub diagnoza
„za mało kroków”. K512 występuje w T-kalibracji, lecz nie w feature optimizer.
Tę różnicę ekspozycji należy odróżnić od samego ograniczenia pojemności.

RFF2048 pozostaje kompetentny na tych samych świeżych danych. Wynik0006
o efekcie delta-versus-additive pozostaje zachowany; to klasyczna reguła
zapisu z wyuczonym transportem. Wynik0007 odrzuca dodatkową recepturę
uczenia mniejszej mapy, nie poprzedni efekt i nie całą rodzinę.
Syntetyczna obserwacja jest ciągła, wymaga fitu transportu względem raw,
lecz legalny ridge/PCA prawie idealnie rozwiązuje zadanie taniej. To ogranicza
przydatność PVM01 do roszczenia o przewadze nad silnym klasykiem.

## CONFIDENCE

Wysoka pewność odrzucenia dokładnej receptury względem zamrożonych gates,
z silnym ujemnym CI retencji. Brak potwierdzonego dodatniego feature-learning
gain; przedziały nie dowodzą dokładnego zerowego efektu. Pięć niezależnych
jednostek nie daje szerokiego transferu lub zewnętrznego niewidocznego holdoutu.
Nie ma wyniku architektonicznej nowości, LLM-successor lub AGI.

## ALTERNATIVES AND PROJECT PROGRESS

MUC zamknięto jako test techniczny z publicznym exact-key symbolic100%.
0001 nie potwierdził hard-negative4096/192;0002 potwierdził wąskie
undertraining,0003 nadal nie osiągnął stabilnej kompetencji przy8192.
Nie wracamy do czwartej receptury steps.0005 ustanowił kompetentny
dense/pointer i kontrolowany efekt uczenia w świeżym PVM.0006 potwierdził
overwrite delta i ujawnił dominację klasyków.0007 sprawdził alternatywę
uczenia samej mapy pamięci i odrzuca jej dokładną wersję.

Możliwe rozróżnienie teraz: ekspozycja feature-fit na duże supporty versus
limit512. Sam wzrost liczby kroków przy obecnej małej CE ma słabe uzasadnienie.
Zmiana beta/pojemności/gate jednocześnie nie izolowałaby przyczyny. Jeśli
uczony transport+RFF2048 nadal przegrywa z ridge/PCA, przyszły uzasadniony
trudniejszy wariant musi mieć zamrożoną kontrolę nieliniowego transportu,
strong retrieval i matched-quality pełne koszty, a nie osłabiony klasyk.
Literatura delta/RFF jest znana: [Schlag et al.2021](https://arxiv.org/abs/2102.11174),
[Rahimi/Recht2007](https://proceedings.neurips.cc/paper/2007/hash/013a006f03dbc5392effeb8f18fda755-Abstract.html).
Motywacja uczenia Fourier features: [Li et al.2021](https://arxiv.org/abs/2106.02795),
zapis SRC0445. Tam positional encoding; obecny minimalny test pamięci nie
jest wierną repliką ani dowodem ich twierdzeń lub nowości.

## DECISION AND NEXT DISCRIMINATING EXPERIMENT

**DISCARD exact RFF512/512-step learned feature recipe**. Kontynuacja programu
pozostaje aktywna;4/17 nowych tickets zużyte,13 pozostaje. Stare3 i2655,336485s
zachowane. Aktualny study terminal, benchmark maintenance,scoring=false.
Dokładnie jeden EXP w tym cyklu; bez retry,WT8–9/API/schedule changes.

Następny ograniczony cykl powinien prospektywnie zamrozić **memory-training
support exposure K32/128 versus including K512**, fixed512 features/512 steps,
source-identical poprawny transport, frozen/shuffled controls, zoptymalizowany
dense i mocne klasyczne/retrieval, pięć nowych sparowanych jednostek T/D.
Przed implementacją ustalić matched query-label counts, stratyfikację supportów,
retained/UNKNOWN/full gates i całe capy. Nie dobierać siatki na obecnym D i nie
zmieniać bramek0007. Jeśli nieuzasadnione, skończony przegląd alternatyw.
Mechanizm wymaga jeszcze niezależnej replikacji, trudnego wariantu, trzech skal
i frozen fresh final. Ekonomiczna non-domination i końcowy cel są niewykonane;
jedna porażka nie zamyka całego programu. Nie rozpoczynamy drugiego EXP tutaj.
"""
target = b / f"research/analyses/{identity}.md"
assert not target.exists()
target.write_text(text, encoding="utf8", newline="\n")
print("Immutable analysis", target.relative_to(b), sha256_file(target))
