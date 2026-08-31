# GEN-1 — WT changepoints acquisition/provenance, cykl 115

Zakres: jeden no-scoring service cycle po source gate z cyklu 114. Pobrano wyłącznie
oficjalne `wt_changepoints_v1`, zweryfikowano archiwum, bezpiecznie rozpakowano lokalnie i
zinwentaryzowano wszystkie rekordy. Nie utworzono benchmarku, evaluatora, schematu, hipotezy,
planu eksperymentu, seeda, kandydata ani wyniku. Nie wykonano scoringu.

## Proweniencja i bezpieczeństwo

- URL: `https://causalchamber.s3.eu-central-1.amazonaws.com/downloadables/wt_changepoints_v1.zip`
- rozmiar: `739333` B, zgodny z HEAD;
- MD5: `7e9f26d192674f2aaa6481f4415007eb`, zgodny z oficjalną stroną i ETag;
- SHA-256: `a247ecd867aadb99f524f4cfcb22ded28e550b069ffd10f4df477c036e8a3979`;
- 11 wpisów ZIP, 5722421 B po ekstrakcji;
- zero rooted paths, `..`, wyjść poza katalog docelowy i symlinków;
- surowe archiwum oraz ekstrakcja pozostają lokalne i gitignored; tracked jest tylko manifest.

## Obserwacje danych

| Własność | Wynik |
|---|---:|
| CSV | 10 (`load_in_seed_0` … `load_in_seed_9`) |
| Łączne wiersze | 20297 |
| Kolumny | 37, identyczny nagłówek |
| Missing / non-finite | 0 / 0 |
| Monotoniczny timestamp | PASS we wszystkich plikach |
| Markery interwencji | 100, dokładnie 10 na plik |
| Marker = rzeczywista zmiana `load_in` | PASS dla wszystkich 100 |
| Poziomy | 0.01: 25, 0.1: 24, 0.2: 27, 0.5: 24 |
| Długość odcinka | 100–297 pomiarów |
| Recurrence | każdy plik zawiera wszystkie cztery poziomy i co najmniej trzy poziomy powtórzone |

Kolumna `counter` jest globalnym indeksem wiersza i nie resetuje się przy zmianie. Pierwszy
audit diagnostyczny oczekiwał resetu i dlatego wyświetlił FAIL, lecz reset nie należał do
prerejestrowanej bramki ani dokumentacji. Dalsza kontrola potwierdziła dokładne zwiększanie
0…N−1; `flag` jest stale zerowy. Nie zmieniono kryterium naukowego po obserwacji.

## Boundary i target leakage

Surowego wiersza nie wolno podać kandydatowi. Zawiera on nowy `load_in`, prywatny marker
`intervention` oraz outcomes zmierzone po zmianie. Bezpieczny prospective prequential boundary
jest możliwy tylko jako chroniona transformacja:

1. przed predykcją kandydat otrzymuje anonimową historię poprzednich obserwacji i bieżącą
   numeryczną wartość jedynego zmienianego sterowania;
2. nie otrzymuje nazw, pliku/seeda, markera, czasu absolutnego, bieżących outcomes ani przyszłego
   harmonogramu;
3. zamrożony outcome vector zostaje ujawniony dopiero po predykcji;
4. dopiero potem wolno wykonać naliczony slot-local update.

Źródło ma wystarczające dane do projektu takiego testu, ale partition kanałów, split, target,
metryki, K i baseline'y nie są jeszcze zamrożone. Cztery poziomy nie są automatycznie czterema K.

## Interpretacja i niepewność

Źródło usuwa blokadę infrastrukturalną: istnieje mały realny system z 100 powtarzanymi
interwencjami i odpowiedziami czasowymi. Nie jest to evidence dla learnera ani LLM-successor
claim. Dane są lokalnie widoczne, więc mogą dać tylko screening; mocna teza nadal wymaga
nieinspekcjonowanego holdoutu.

Confidence `0.995` dla integralności i recurrence danych. Confidence `0.85`, że można zbudować
family-blind prequential task bez ręcznej ontologii niosącej rozwiązanie; niepewność dotyczy
zamrożenia outcome channels, odporności na trywialny odczyt poziomu oraz mocnych klasycznych
kontrolek.

## Decyzja

`keep_for_service_design_gate`. Zachować lokalne dane i tracked manifest. Nie tworzyć jeszcze
HYP-0028 ani EXP-20260831-0006 i nie uruchamiać scoringu.

## Następny rozstrzygający krok

Następny wake może wykonać dokładnie jeden no-scoring **prequential contract design gate** na
zamrożonym manifeście. Bez implementacji evaluatora ma z góry ustalić albo odrzucić:

- whole-file train/development/test split bez nakładania sekwencji;
- lossless anonymous query/reveal/update tuple i mechaniczny channel partition;
- co najmniej trzy sensowne K oparte na dostępnej historii, nie na poziomie targetu;
- OOD split obejmujący niewidziane przejścia poziomów lub długości odpowiedzi;
- jakość, stability, update locality i pełne R1/R4/R16 cost axes;
- persistence, no-update, LMS, RLS/Kalman, change-point model bank oraz bounded replay controls;
- target-leakage, level-router, seed/file classifier i future-schedule invalidation fixtures.

Jeśli silny klasyczny model rozwiązuje task trywialnie, anonymous partition wymaga semantycznej
ontologii albo OOD nie jest identyfikowalne z 10 sekwencji, zapisać `reject_before_benchmark`.
Tylko pełny PASS może w osobnym późniejszym wake uzasadnić chronioną kohortę; nadal nie zezwala
na hipotezę ani scoring.
