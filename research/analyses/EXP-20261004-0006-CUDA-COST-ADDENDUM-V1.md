# EXP-20261004-0006 — uzupełnienie kosztu pamięci CUDA

Tabela głównej analizy zawiera logiczny stan i peak RSS procesu. Poniżej dodano odczyty szczytu alokatora CUDA z wszystkich75 zachowanych dzienników device. Są to maksima z całego workera, obejmujące fit i ewaluację. Nie izolowano bieżącej rezerwacji CUDA podczas samej inferencji CPU i nie twierdzimy, że proces wcześniej trenujący na GPU ma wtedy zerową zajętość GPU. Odczyty PyTorch nie obejmują całej pamięci sterownika/kontekstu ani innych procesów. Energia nie była mierzona. Żadne wyniki, źródła naukowe lub bramki nie zmieniły się.

| Metoda | Średni peak allocated MiB | Średni peak reserved MiB | Zakres reserved MiB |
|---|---:|---:|---:|
| additive | 67.741 | 68.000 | 68.000–68.000 |
| delta | 67.741 | 68.000 | 68.000–68.000 |
| delta_shuffled | 67.741 | 68.000 | 68.000–68.000 |
| delta_untrained | 0.080 | 2.000 | 2.000–2.000 |
| dense | 75.997 | 94.000 | 94.000–94.000 |
| dense_cached_cpu | 75.997 | 94.000 | 94.000–94.000 |
| dense_cached_cuda | 75.997 | 94.000 | 94.000–94.000 |
| exact_nn_cpu | 67.741 | 68.000 | 68.000–68.000 |
| kernel | 0.000 | 0.000 | 0.000–0.000 |
| pointer | 67.741 | 68.000 | 68.000–68.000 |
| raw | 0.000 | 0.000 | 0.000–0.000 |
| ridge | 0.000 | 0.000 | 0.000–0.000 |
| ridge32 | 0.000 | 0.000 | 0.000–0.000 |
| ridge_pca_scan | 0.000 | 0.000 | 0.000–0.000 |
| ridge_pca_tree | 0.000 | 0.000 | 0.000–0.000 |

Pełne wartości pięciu jednostek, ścieżki i hashe: research/reviews/EXP-20261004-0006-CUDA-COST-DIAGNOSTICS-V1.json.
