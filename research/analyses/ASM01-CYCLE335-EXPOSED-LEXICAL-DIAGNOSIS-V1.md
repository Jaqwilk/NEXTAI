# ASM01 — cykl335: diagnoza znanego pliku

**KEEP: diagnoza leksykalna. INCONCLUSIVE: naukowe porównanie ASM01.**

Prerejestracja V3 została zamrożona w69aa3db przed driverem; źródła wykonania w0e931cb przed pierwszym uruchomieniem. V1 i V2 nie uruchomiły testów ani odczytu. V3 używa dokładnie niezmienionego klasyfikatora V2 i tych samych czterech krótkich identyfikatorów fixtures. Poprawka licznika seriali była zamrożona przed pierwszym testem. Nie zmieniono parsera trajektorii, normalizera, geometrii, modeli ani progów.

W niezależnym klonie wszystkie4/4 syntetyczne przypadki przeszły: categories, metadata, malformed i provenance. Dopiero potem jeden raz odczytano wcześniej ujawniony plik17:74, po sprawdzeniu jego hash oraz wszystkich zamrożonych zależności. Klasyfikator nie konwertuje współrzędnych na liczby i nie emituje nazw ani tokenów.

Z175 wierszy punktów wszystkie X są unsigned. Y:172unsigned,3minus_nonzero,0exact_minus_zero,0other_minus_zero,0other. Wszystkie liczniki błędów obwiedni, liczby stroków, nagłówka, markerów, nieznanych wierszy, stanu i seriali oraz spadku serialu wynoszą0. Ujemne tokeny nie są żadnym zapisem zera. To wystarczający dowód niezgodności tego pliku z zamrożoną unsignedXY/regułą dolnej granicy0; diagnoza nie ustala innych potencjalnych problemów zbioru.

Nie stosujemyabs, clamp, przesunięcia, zamiany próbek ani zmiany geometrii. Nie kontynuujemy native intake. Zero nowych próbek, numerycznych konwersji, wywołań parsera/normalizera/geometrii, NPZ, fit, rejestracji i EXP. Nie wolno interpretować intake failure jako negatywnego wyniku uczenia, transferu lub ekonomii. Zachowano wcześniejsze74 dokładne zgodności i1171 walidowane konwersje z332 oraz wszystkie niepowodzenia i niewykonane zakresy333/334.

Jeden boundedjob trwał0.3972502999822609s, exit0;5 utworzonych procesów,0 aktywnych i0 żywych potomków na wyjściu. Pełny etap nalicza300s od04:03 do04:08Z, obejmujące prerejestrację, kod, klon, test, znany plik, analizę, zapis i publikację. Jest to konserwatywny koszt pełnego etapu, nie sam czas testu. Pozostałe niechronione B:230.4497597999289s. Chronione7rejestracji/47000s bez zmian. Źródła, wyniki XML/stdout/stderr i hash-bound receipt oraz losslessZIP zachowane.

Pełny cel pozostaje ACTIVE/INCOMPLETE. Brakuje zakończonej drugiej naukowej rodziny transferu, niezależnych replikacji i świeżych finałów B oraz ocenionego lokalnego prototypu fact/source/update/UNKNOWN. Kontrakt B dopuszcza uzasadnioną alternatywną rodzinę po nowej prerejestracji; jej screen nie może konsumować chronionych rezerw. Nie zakładamy, że230.45s wystarczy na nowy intake, conformance, modele i pełne porównanie. Nie przenosimy chronionych środków bez nowej authority. Read-only audit pozostałych dozwolonych etapów jest odrębny od tej diagnozy.
