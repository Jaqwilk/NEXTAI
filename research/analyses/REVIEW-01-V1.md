# REVIEW-01-V1 — decyzja po R0, PC-01 i WT-01

Status: ukończony przegląd przygotowawczy, bez treningu i scoringu. Proponowany,
nieaktywny kontrakt: `research/plans/MUC-01-PROPOSED-CONTRACT-V1.json`.

## OBSERVATION

| Pytanie | Dowód | Ograniczenie | Koszt / stan | Decyzja |
|---|---|---|---|---|
| Czy aparatura zachowuje pochodzenie i historię? | R0 w cyklu 283: 689 testów, `doctor` i integralność przeszły; historyczne hashe i prefiksy ledgerów zachowano; provenance odzyskało trzy zależności WT z Git. | Test checkoutu był na Windows, nie na natywnym Linux; zignorowane payloady danych trzeba było skopiować lokalnie. | Etap wyłącznie serwisowy, bez EXP i scoringu. | KEEP: R0 wystarcza do interpretowania kolejnych lokalnych wyników, nie dowodzi jakości modelu. |
| Czy kontrola uczenia działa? | PC-01: trzy finalne seedy dały średni kontrast frozen−trained 5.5741 bpb, dolną jednostronną granicę 95% 5.4392 bpb i trained 2.4809–2.5144 bpb. Wszystkie progi i kontrole przeszły. | Jeden dostępny korpus; zależne okna bajtowe; brak transferu i porównania ekonomicznego z matched-quality klasycznym systemem. | 893.845 s final fit, 2394.271/7200 s łącznie; maks. RSS 1.503 GB i CUDA reserved 2.175 GB. | KEEP jako wysokiej pewności lokalną kontrolę uczenia; bez promocji architektury. |
| Co wyjaśnia dodatni WT? | EXP-20260906-0001: 162/162 stabilnych prób; kontrast rekurencji 0.16279 NRMSE, dodatni na plikach 6 i 7. | Dwa wcześniej widoczne nagrania, jeden seed permutacji, zero niezależnych replik fizycznych. | Query ops wzrosły 470→22560; przy R16 workload 10.31M→16.67M. | KEEP tylko jako opisową atrybucję na visible development. |
| Czy WT wskazuje nowy mechanizm? | Kontrola VAR(2)/ARX była zgodna z R1-U1-C1 do 3.55e-15. | Klasyczne wyjaśnienie jest kompletne; brak przewagi kosztowej. | Rekurencja była droższa. | Nie przenosić WT do następnego prototypu; HYP-0028 pozostaje dormant. |

EXP-20260906-0001 jest terminalny, wynik i analiza są niezmienne, nie ma pending
planu, a lokalny `master`, `origin/master` i `origin/main` wskazywały przed tym
etapem commit `0d8a689ac5714784e0328a3960a5c2b26724efcb`. Eksperymentu nie powtórzono,
a plików WT 8–9 nie otwarto.

## INTERPRETATION

Pierwszy pakiet spełnił swój cel aparaturowy. Wiemy, że harness umie wykryć
uczenie oraz izolować czynnik, ale nie mamy jeszcze dowodu lepszej architektury.
WT nie jest dobrym składnikiem domyślnym następnego systemu: jego dodatni efekt
ma równoważne klasyczne wyjaśnienie i zwiększa koszt zapytania.

Najtańsze następne pytanie powinno zatem bezpośrednio testować lokalne zastąpienie
faktu i kompozycję przy rosnącym K. Proponowany Mutable Contact Ledger ma
oryginalny generator, dokładną odpowiedź i pełny krzyż K=32/128/512 z D=1/2/4.
Nie wymaga danych zewnętrznych ani LLM-as-a-judge. Jedynym badanym mechanizmem
jest delta-update w pamięci fast-weight. Źródłowo identyczna ablacją append-only
oddziela ten efekt od zwykłego wyszukiwania, a jawny parser+hash-map pokazuje,
czy uczenie tylko drogo odtwarza reguły benchmarku.

## ŹRÓDŁA PIERWOTNE I DOSTĘPNOŚĆ

- LongMemEval publikuje 500 pytań o wydobywanie informacji, aktualizacje wiedzy,
  rozumowanie wielosesyjne/czasowe i abstencję oraz warianty około 115 tys.
  tokenów i 500 sesji. Repozytorium dokumentuje pliki na Hugging Face, ale jego
  ewaluacja odpowiedzi używa GPT-4o/OpenAI API. Dlatego wykorzystujemy tylko
  metodę timestampowanych aktualizacji, nie dane, modele ani judge.
- Oficjalny generator bAbI udostępnia regulowaną liczbę faktów wspierających i
  decoyów, lecz repozytorium jest zarchiwizowane. CLUTRR rozdziela długość relacji
  i niewidziane wzorce kompozycji, ale kod/dane są CC BY-NC 4.0. Oba są tylko
  inspiracją metodologiczną; nowy generator ma własne zdania i semantykę.
- RAG, End-To-End Memory Networks i fast-weight programmers są bezpośrednim
  prior art dla retrievalu, wielohopowej pamięci i delta-rule. Pozytywny wynik
  nie będzie więc twierdzeniem o nowości tych składników.

Nie pobrano żadnego zbioru, modelu, kodu ani zależności.

## CONFIDENCE

Wysoka dla granic wniosków z R0/PC-01/WT-01 i wykonalności samego syntetycznego
kontraktu. Umiarkowana dla osiągalności progów w zamrożonym czasie: najdłuższy
kontekst i cztery role uczone wymagają testu wykonalności przed przyszłym EXP.
Niska dla oczekiwanej przewagi ekonomicznej; mocna kontrola symboliczna może
zdominować wszystkie modele i taki wynik ma być zachowany jako prawidłowy negatyw.

## ALTERNATIVE EXPLANATIONS

Lepszy wynik pamięci delta może pochodzić z pojemności, regularizacji albo innej
łatwości treningu, a nie z lokalnego zastępowania. Dlatego kandydat i ablacją
dzielą encoder, kontroler, wymiar, tokenizer i budżet, a wymagany efekt dotyczy
zapytań jednocześnie aktualizowanych i kompozycyjnych. Różnica czasu może wynikać
z niezoptymalizowanej implementacji baseline'u; wszystkie role mają przejść
testy kompetencji i zachować surowe próbki. Generator może faworyzować parser;
jest to jawne ograniczenie zadania i powód, by oddzielić mechanizm od twierdzenia
o uniwersalnej ekonomii.

## DECISION

KEEP pakiet aparaturowy i przedstaw `MUC-01-PROPOSED-CONTRACT-V1` do decyzji.
Nie replikować teraz WT i nie budować integracji z jego rekurencją. Nie aktywować
MUC-01 bez osobnej zgody. Dodatni przyszły pojedynczy seed byłby tylko screeningiem;
ujemny przy ważnych kontrolach zamyka dokładnie tę wersję delta-memory.

## INTEGRITY AND BUDGET

REVIEW-01 zużywa jeden z jednego cyklu przygotowawczego i konserwatywnie całe
60/60 minut. Zużycie EXP/trening/scoring/download/WT-8–9 wynosi zero. Historyczne
plany, wyniki, analizy i ledgery pozostają append-only. Harmonogram nie został
zmieniony. Aktualna kolejka po walidacji to `REVIEW-01-DECISION`.

## NEXT DISCRIMINATING EXPERIMENT

Nie ma obecnie autoryzowanego eksperymentu. Po osobnej decyzji najpierw jeden
cykl implementacji bez scoringu (maks. 60 min) ma zbudować generator, role,
conformance i test wykonalności 8192 tokenów. Dopiero po dwóch maksymalnych
próbach dev i zamrożeniu recipe wolno byłoby zarejestrować jeden jednoseedowy
screen MUC-01, bez retry i bez automatycznej promocji.
