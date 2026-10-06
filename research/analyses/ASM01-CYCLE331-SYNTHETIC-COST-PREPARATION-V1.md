# ASM01 — cykl331: zamrożony syntetyczny pomiar kosztów

Prerejestracja b8d4835 przed implementacją i jedynym pomiarem w klonie.
Pełny screen niezmienionych45roles/810trials wymaga32040 DTW calls i1007380 transformów, poza intake/old74 checks.
Probe wykonał48 DTW calls (16/K16/32/64) i144 transformy (16×3lengths39/213/691×3views), wszystkie z pierwszym wywołaniem. Sprawdzano kształt, dtype i finite; nie oceniano jakości. Complete=True.

Prognoza inżynierska seconds: {'DTW': 246.40255206730217, 'cross_family_HAR_residual': 361.10048040014226, 'total_worker_proxy': 884.7340085004689, 'transform': 277.2309760330245}. Decyzja: **KEEP runtime evidence only**.
Zamrożona formuła2×10680×sum(maxDTW/K)+2×1007380×max(transform)+2×HAR180.5502402; próg worker1000s, przyszły wholecap2200 zaux1200. Mnożnik2 i historyczny HAR residual nie stanowią statystycznego ograniczenia kosztów ASM. Maxima małej próbki zależą od obciążenia maszyny; zimne wywołania pozostają w danych. Nie ma gwarancji kosztu kalibracji, innych40workers, intake/checks ani administracji.

Koszt całego etapu od03:27Z, obejmujący odczyty/delegację/prerejestrację/kod/pomiar/Git/raport: konserwatywnie600/600s, fit0/EXP0. Cutoff=415.773s; closing jest wewnątrz600. Jedyny job i jego potomkowie: {'complete': True, 'created_at': '2026-10-06T03:33:46Z', 'result': {'elapsed_seconds': 1.857439700019313, 'exit_job_active_process_count': 0, 'exit_live_descendant_pids': [], 'peak_tree_rss_bytes_sampled': 429735936, 'pid': 10324, 'processes_created': 3, 'reason': 'exited', 'returncode': 0, 'root_returncode': 0}}. Rezerwa7tickets/47000s zachowana; pozostałe niechronione B=2267.449760s.

Nie zmieniono modeli, geometrii, gridów, bramek, aktywnego loadera ani starych wyników. Bez nowych nativebytes, NPZ, fitu, rejestracji, retry, WT8–9, futurewriters, externalmodel/API i zmian harmonogramu. Dawny Labtimeout zachowany i nie powtórzony.

Wynik jest wyłącznie dowodem kosztu skończonego syntetycznego probe. Nie dowodzi native1830 feasibility, zgodności old74 ani drugiej rodziny transferu. Pełny cel pozostaje ACTIVE: transfer, niezależne replikacje, świeże finały i lokalny fact/source/update/UNKNOWN prototype są niedokończone. Następny scope wymaga nowej prerejestracji i finansowania przed nowymi bytes/code; jeśli koszt nie jest uzasadniony, nie wolno zmieniać DTW/modeli/gate po pomiarze ani konsumować chronionej rezerwy.

Surowe latencje, bindingi i źródła: research/laboratory/archive/ASM01-SYNTHETIC-COST-EVIDENCE-V1.zip. Receipt: research/laboratory/ASM01-COST-PREP-COMPLETION-V1.receipt.json.
