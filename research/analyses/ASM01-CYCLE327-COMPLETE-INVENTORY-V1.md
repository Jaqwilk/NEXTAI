# ASM01 — cykl327: pełna inwentaryzacja struktury

Zamknięto 2026-10-06T01:59:05Z. Nowy EXP: **brak**; ostatni EXP-20261005-0007.
Plan `research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.json`, SHA256 `730a9e6843eaf085970bad82e5878dc404f400634e0c8ff18ab9af0e4c46888d`. Prerejestracja cfc8667; źródło fce7d49,
70-case proof05e57ed i pełny dowód metadanych8fecc22 poprzedzają jedyny odczyt.
Pełny cel pozostaje **ACTIVE**; maintenance, scoring=false.

## OBSERVATION

W niezależnym klonie zakończono **1830/1830** plików i **407424/407424** niepustych
wierszy; każdy wiersz ma kategorię i zapis formy. Nieznane wiersze: **0**.
Ponownie otwarto75 znanych tekstów, pierwszy raz1755; D:915. Wszystkie1830 SHA zachowano.
389510 wierszy ma formę punktową,5304 PEN_DOWN,5290 PEN_UP i po1830 czterech nagłówków.
Nie odczytano numerycznie X/Y; nie wykonano parsera, modelu, NPZ, fitu lub rejestracji.

**55 plików ma anomalie**: T24, D31. Liczniki wierszy/zdarzeń: incomplete lifecycle19,
pen-up-without-stroke2, repeated-down1, point-outside-stroke33, serial-mismatch345,
point-lexical-form3. Te liczniki nie oznaczają niezależnych jednostek lub błędnych współrzędnych.
W1/sample75 ma pojedynczy punkt stanu1/serial2 po adnotacji PEN_UP; zachowano pełny rekord.
Jedynie W17/sample74 zawiera3 formy Y=`negative_integer`. Konkretne tokeny i wartości są
**nieznane**: forma obejmuje także `-0`. Nie stwierdzono ujemnej wartości numerycznej.

**70/70** syntetycznych przypadków i **1/1** lifecycle PASS. Pełny końcowy Lab,
w tym Doctor: errors=[],warnings=[]. Hash wszystkich **1453 zamrożonych** plików obu kopii PASS;
pełny manifest klonu PASS. Nowe, odrębnie zatwierdzone pliki MUC w oryginale są poza cyklem327;
nie sprawdzano ich przez dawną ścisłą listę i nie użyto ich w końcowym jobie klonu.
Pierwszy startup Doctor nie uruchomił kontroli przez odmowę domyślnego cacheuv;
exit2 i pełne54s zachowano. Osobno zamrożona lokalna ścieżka cache przeszła kontrolę.
Wszystkie nadzorowane drzewa zakończone bez żywych potomków. Pełnej regresji nie powtarzano;
timeout46% z cyklu321 pozostaje niezaliczony. Dawny intake75prób/74konwersje/D0 niezmieniony.

## INTERPRETATION

Alias końcowego `.txt`/`.TXT` zachował wszystkie UID i umożliwił pełną strukturę.
Niektóre adnotacje pióra są niespójne z jawnym polem stroke. Jest to diagnoza serializacji,
nie wynik uczenia, UNKNOWN lub kosztu inferencji. Nie ma nowego wyniku naukowego ani CI.

## CONFIDENCE

Wysoka dla kompletności tej skończonej inwentaryzacji i form leksykalnych. Nieustalona
dla wartości podpisanych Y, monotoniczności wszystkich seriali, geometrii i skutków transferu.
Histogram seriali nie zachowuje kolejności. Przyszła korekta granic może zmienić deduplikację,
liczbę punktów i parzystość widoków; nie wolno nazywać jej równoważną bez testu zgodności.

## DECISION

**KEEP** kompletną strukturę i walidację techniczną; **INCONCLUSIVE** porównanie naukowe.
Zapisano wyłącznie przyszłą propozycję `research/plans/ASM01-POINT-SERIAL-METADATA-PROSPECTIVE-V1.json`; bez implementacji lub retry.
Tylko literalne `-0→0` może być jawnie dopuszczoną reprezentacją tego samego zera.
Nie wolno akceptować innych znaków, clamp/abs/offset ani usuwać próbek/punktów.
Niewykonalność konkretnych bramek zamyka ten przepis i uzasadnia odrębną licencjonowaną rodzinę.

| Pełny koszt pomocniczy, w tym nieudany startup | Sekundy |
|---|---:|
| NEXTAI-B-327-startup-doctor | 54 |
| NEXTAI-B-327-startup-doctor-local-cache | 218 |
| NEXTAI-B-327-startup-lab | 260 |
| NEXTAI-B-327-administration-prepaid | 300 |
| NEXTAI-B-327-precontent-seal-V1 | 127 |
| NEXTAI-B-327-inventory-fixtures-V1 | 65 |
| NEXTAI-B-327-fixture-proof-V1 | 56 |
| NEXTAI-B-327-real-metadata-V1 | 55 |
| NEXTAI-B-327-native-inventory-V1 | 57 |
| NEXTAI-B-327-clone-lab-lifecycle-V1 | 371 |

Łącznie **1563/1800s**; rezerwacje rozliczone. B: **1/12**, **20098.550240200071/72000s**.
Chronione **7rejestracji/47000s**; margines niechroniony **4901.449759799929s**.
A i MUC pozostają zamknięte i zużyte. Bez WT8–9, zewnętrznych modeli/API i zmiany harmonogramu.

## NEXT DISCRIMINATING EXPERIMENT

Prospectively freeze a NEW bounded metadata-only serialization study before code or renewed native access: explicit monotonically nondecreasing positive point stroke IDs are authoritative, all X/Y/state/serial rows and order retained, declared empty strokes preserved. Only literal coordinate -0 may alias0; reject every other signed coordinate or ambiguous/nonmonotone/out-of-range ID. Require exact old accepted-array and write/nominal/adverse descriptor equality, unchanged dedup/geometry/bounds/byte caps, complete1830 hash-bound feasibility and no filtering before a separately frozen scientific cohort/readiness/one audited EXP. Negative lexical Y remains numerically unknown. Any nonzero signed value, impossible geometry, changed old array or ambiguous IDs closes this exact route without rescue; assess a distinct licensed native family prospectively. Current user-requested independent MUC stage is separate and does not rewrite ASM results. Preserve future7tickets/47000s and full transfer/replication/fresh-final/prototype goal.

Druga rodzina, niezależne replikacje, świeże finały i lokalny prototyp nadal wymagają dowodów.
