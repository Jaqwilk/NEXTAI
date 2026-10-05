<p align="center">
  <img src="docs/assets/nextai-banner.svg" alt="NEXTAI — badania nad inteligencją na jednostkę obliczeń" width="100%">
</p>

<h3 align="center">Laboratorium badawcze, w którym dowody mają pierwszeństwo przed architekturą.</h3>

<p align="center">Zarejestruj pytanie. Sprawdź mechanizm. Policz pełny koszt. Zachowaj dowody.</p>

<p align="center">
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.12 lub nowszy"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/PyTorch-2.6.0-EE4C2C?style=flat-square&amp;logo=pytorch&amp;logoColor=white" alt="PyTorch 2.6.0"></a>
  <a href="docs/SCIENTIFIC_PROTOCOL.md"><img src="https://img.shields.io/badge/Scientific_protocol-v3-D7A649?style=flat-square" alt="Protokół naukowy w wersji 3"></a>
  <a href="docs/CURRENT_STATUS.md"><img src="https://img.shields.io/badge/Stage-experimental-697586?style=flat-square" alt="Etap badań eksperymentalnych"></a>
</p>

<p align="center">
  <a href="#szybki-start">Szybki start</a> ·
  <a href="#wyniki-badań">Wyniki badań</a> ·
  <a href="#jak-działa-laboratorium">Jak to działa</a> ·
  <a href="#dokumentacja">Dokumentacja</a> ·
  <a href="README.md">English</a>
</p>

---

## Pytanie badawcze

**Czy użyteczna inteligencja może wymagać mniej obliczeń, gdy rośnie ilość przechowywanej wiedzy?**

NEXTAI szuka zasad obliczeniowych, które mogłyby poprawić zdolności na jednostkę **pełnego kosztu inferencji** względem gęstych autoregresyjnych modeli językowych. Badania obejmują pamięć strukturalną, uczony retrieval, lokalne aktualizacje, adaptacyjne obliczenia, modele przyczynowe i mechanizmy oparte na programach.

Repozytorium łączy lokalny harness eksperymentalny w Pythonie z wersjonowaną historią badań. Codex wnosi ocenę naukową w bieżącym czacie; pakiet odpowiada za prerejestrację, pomiary, integralność i trwałe rozliczenia. Oceniani kandydaci nie wywołują zewnętrznego modelu ani API modelowego.

Długoterminową ambicją jest inna architektura obliczeniowa AI. Obecnym rezultatem jest eksperymentalne laboratorium i zgromadzone dowody: **żadna architektura nie została promowana i nie wykazano przewagi nad czołowymi LLM.**

## Co zawiera projekt

| Element | Do czego służy | Gdzie zajrzeć |
| :--- | :--- | :--- |
| **Harness eksperymentalny** | Audytuje zależności kandydatów, sprawdza zamrożone źródła, uruchamia ograniczone workery i zapisuje surowe próby. | [Runner](src/nextai_autoresearch/runner.py) · [CLI](src/nextai_autoresearch/cli.py) |
| **Biblioteka kandydatów** | Bada pamięć, retrieval, rekurencję, przyczynowość, kompresję i wykonywanie programów. Zawiera kontrole uczone, klasyczne, losowe i oracle. | [Kandydaci](src/nextai_autoresearch/candidates/) · [Katalog idei](docs/IDEA_CATALOG.md) |
| **Wersjonowane zadania** | Rozdziela kohorty benchmarków, legalne obserwacje, zbiory treningowe i granice ewaluacji. | [Benchmarki](src/nextai_autoresearch/benchmarks/) · [Schematy](schemas/) |
| **Pełne pomiary kosztu** | Rozlicza fit, ingest, indeksowanie, aktualizacje, zapytania, dekodowanie, stan i koszty zależne od sprzętu. | [Metryki](docs/METRICS.md) |
| **Historia badań** | Zachowuje prerejestracje, wyniki, analizy, porażki, budżety i archiwa ocenianego kodu. | [Raport](research/REPORT.md) · [Model danych](docs/DATA_MODEL.md) |

## Szybki start

### 1. Pobierz repozytorium

```powershell
git clone https://github.com/Jaqwilk/NEXTAI.git
cd NEXTAI
```

Potrzebujesz **Pythona 3.12+** i wcześniej zainstalowanego **uv**. Aktualne receptury badań PVM wymagają karty NVIDIA z CUDA; samo czytanie wyników lub przegląd CLI to osobne czynności. Przypięte środowisko używa PyTorch 2.6.0 z indeksu pakietów CUDA 12.4.

### 2. Przygotuj przypięte środowisko

Bootstrap szacuje rozmiar instalacji i cache oraz wymaga, by **pozostało co najmniej 10 GiB wolnego miejsca**. Instaluje zależności developerskie z lockfile i uruchamia `doctor`:

```powershell
python scripts/bootstrap_environment.py
```

Jeśli budżet dysku został już sprawdzony, właściwe polecenie instalacyjne to:

```powershell
uv sync --frozen --extra dev
```

Duże dane benchmarków i checkpointy pozostają lokalnie. Bootstrap nie pobiera zbiorów badawczych ani pretrained modeli. Nowy komputer może zgłosić brak lokalnych plików; sprawdź dokumentację pozyskania danych w [research/data](research/data/) zamiast podmieniać zbiór.

### 3. Sprawdź laboratorium

```powershell
uv run nextai --help
uv run nextai doctor
uv run nextai lab status
```

`doctor` sprawdza spójność. `lab status` pokazuje zweryfikowaną kolejkę, aktualne uprawnienia, zużyte próby i pozostały budżet obliczeń. **Pozytywna kontrola nie uprawnia do nowego eksperymentu.**

W przygotowanym środowisku badawczym regresję uruchamia `uv run pytest`. Część kontroli zależy od lokalnych plików i zachowania Windows/CUDA; sam czysty klon nie gwarantuje odtworzenia każdego historycznego uruchomienia.

## Wyniki badań

**Stan po zakończeniu cyklu 311, zapisany 4 października 2026 (UTC).** Program kontynuacji jest aktywny; bieżący benchmark pozostaje w maintenance, z `scoring=false` i bez oczekującego płatnego uruchomienia. [Aktualny status](docs/CURRENT_STATUS.md) opisuje zakończone prace, a `uv run nextai lab status` wyznacza wiążącą bieżącą kolejkę.

Najnowsze badania PVM sprawdzają, czy system potrafi połączyć **dwa zaszumione widoki tożsamości**, odpowiadać z aktualizowanej pamięci, zachować niezmienione fakty i odrzucać nieznane tożsamości. Rozmiary pamięci to **32 / 128 / 512**, a rundy aktualizacji **0 / 1 / 4**. Rundy aktualizacji nie oznaczają głębokości rozumowania.

| Badanie | Zapisana obserwacja | Decyzja i jej zakres |
| :--- | :--- | :--- |
| [Kontrola uczenia · 0005](research/analyses/EXP-20261004-0005.md) | Dokładność pełnej odpowiedzi dense: **99,9861%**; pointer i ridge: **99,9722%**, na pięciu świeżych sparowanych jednostkach seed/dane. | **KEEP** lokalną kohortę screeningową. Ridge osiąga jakość pointer przy znacznie niższym zmierzonym koszcie workloadu CPU. |
| [Pamięć delta · 0006](research/analyses/EXP-20261004-0006.md) | Poprawność odpowiedzi po aktualizacji rośnie z **39,83% do 100%** względem zapisów addytywnych; gain **+60,17 pp**, jednoczesny 98,75% CI **[56,90; 63,43] pp**. | **KEEP** wąski mechanizm delta. Silne kontrole klasyczne nadal dominują ekonomicznie. |
| [Kompaktowe cechy · 0007](research/analyses/EXP-20261004-0007.md) | Dokładność pełnej odpowiedzi wariantu uczonego: **90,7778%**, zamrożonego: **90,8056%**; cztery kryteria pierwotne nie przechodzą. | **DISCARD** tę konkretną recepturę z 512 cechami. Wynik nie falsyfikuje całej rodziny architektur. |
| [Ekspozycja pojemności · 0008](research/analyses/EXP-20261004-0008-ADDENDUM-V1.md) | Zakończono 80 workerów i 720 prób, ale dokładna zgodność dekoderów dense/cache nie przechodzi dla żadnej z pięciu jednostek. | Porównanie **INCONCLUSIVE**. Identyczne decyzje nie naprawiają niespełnionej bramki zgodności. |
| [Zgodność techniczna · cykl 311](research/analyses/PVM01-REPRO-PREPARATION-ADDENDUM-V1.md) | **36/36** poprawionych procesów na stałych fixture; **18/18** deterministycznych fitów z dokładną zgodnością; **1127** testów pełnej regresji przechodzi. | **KEEP** naprawę techniczną. To pomocnicza walidacja zgodności, nie nowy dowód naukowy lub ekonomiczny. |

Każdy wiersz dotyczy osobnego zamrożonego porównania. Te liczby **nie tworzą wspólnego leaderboardu**; pojedyncze pytania, epizody i workery nie są niezależnymi replikami. Raporty zachowują dokładne receptury, niepewność, koszty, ograniczenia i nieudane kontrole.

<details>
<summary><strong>Co jeszcze wymaga dowodu?</strong></summary>

Cel całego programu pozostaje otwarty. Potrzebne są:

- Trudny wariant zadania, który rozróżni proponowany mechanizm od silnych alternatyw klasycznych.
- Porównanie ekonomiczne przy dopasowanej jakości, pełnym koszcie i trzech skalach.
- Niezależna replikacja oraz zamrożona receptura oceniona na świeżych jednostkach finalnych.
- Osobne dowody dla transferu, nowości i szerszych twierdzeń o architekturze.

Proponowane kolejne ograniczone pytanie dotyczy uczonego transportu i pamięci PCA względem silnych kontroli klasycznych i dense, z prerejestrowaną interakcją szumu. To propozycja, nie zakończone badanie ani aktywne uruchomienie.

</details>

## Jak działa laboratorium

<p align="center">
  <img src="docs/assets/research-loop.svg" alt="Przebieg badania: pytanie, prerejestracja, audyt i freeze, ograniczone uruchomienie, dowody, decyzja; wynik prowadzi do kolejnego pytania." width="100%">
</p>

1. **Postaw pytanie rozstrzygające.** Określ mechanizm, konkurencyjne wyjaśnienia i obserwację, która przemawiałaby przeciw hipotezie.
2. **Prerejestruj przed implementacją i danymi.** Zamroź zadanie, recepturę, kontrole, siatki, metryki, bramki, politykę seedów i skończone koszty.
3. **Przeprowadź audyt i freeze.** Sprawdź importy kandydatów, granice danych, hashe źródeł, semantykę baseline'ów i preflight.
4. **Uruchom w zatwierdzonym zakresie.** Użyj audytowanego runnera, ograniczonych workerów i świeżych sparowanych jednostek. Nieudane próby pozostają zużyte.
5. **Zachowaj dowody i podejmij decyzję.** Zapisz surowe wyniki, przeanalizuj niepewność i zachowaj, odrzuć lub uznaj porównanie za nierozstrzygające.

Uczenie, ekonomia i transfer to **osobne twierdzenia**. Użyteczny lokalny mechanizm może przejść swój test i przegrać kosztowo z ridge regression. Nieważne porównanie pozostaje nierozstrzygające nawet przy atrakcyjnej dokładności.

Granica inferencji obejmuje kodowanie, retrieval, przemieszczanie pamięci, obliczenia, dekodowanie i obowiązkową obsługę stanu/cache. Raportowane są także trening, budowa indeksu i aktualizacje, z jawnie określoną amortyzacją. Liczba operacji nie jest zmierzoną energią, a przepustowość batcha nie jest opóźnieniem pojedynczego zapytania.

Pełne kontrakty opisują [protokół naukowy](docs/SCIENTIFIC_PROTOCOL.md), [architektura](docs/ARCHITECTURE.md) i [metryki](docs/METRICS.md). Wcześniejsze opisy etapów w dokumentach pozostają historią; aktualnymi pracami sterują najnowszy status i zweryfikowana kolejka CLI.

## Mapa repozytorium

```text
NEXTAI/
├── src/nextai_autoresearch/
│   ├── candidates/       Mechanizmy obliczeniowe i kontrole porównawcze
│   ├── benchmarks/       Wersjonowane kohorty ewaluacyjne
│   ├── cli.py            Lokalne polecenia nextai
│   ├── runner.py         Audytowane wykonywanie eksperymentów
│   └── integrity.py      Manifesty chronionych źródeł i weryfikacja
├── tests/                Regresje pomiarów, cyklu życia i integralności
├── schemas/              Kontrakty planów, wyników i trwałego stanu
├── config/               Konfiguracja badań i semantyka baseline'ów
├── scripts/              Bootstrap, kontrole zgodności i analizy
├── research/
│   ├── plans/            Niezmienne prerejestracje
│   ├── results/          Surowe próby i agregaty
│   ├── analyses/         Interpretacja naukowa i decyzje
│   ├── laboratory/       Zgody, receipts i archiwa ocenianych źródeł
│   └── REPORT.md         Generowany raport rozdzielony według kohort
├── docs/                 Protokół, metryki, architektura i kontekst badań
├── AGENTS.md             Aktualne uprawnienia i niezmienniki naukowe
└── program.md            Ograniczone cykle i warunki zatrzymania
```

## Dokumentacja

| Zacznij tutaj | Co znajdziesz |
| :--- | :--- |
| [Aktualny status](docs/CURRENT_STATUS.md) | Najnowsze zakończone prace, ograniczenia i kolejne pytanie. |
| [Raport badawczy](research/REPORT.md) | Wyniki według kohort i provenance w [REPORT.provenance.json](research/REPORT.provenance.json). |
| [Protokół naukowy](docs/SCIENTIFIC_PROTOCOL.md) | Prerejestracja, uczciwe kontrole, standard dowodów i granice twierdzeń. |
| [Metryki i rozliczenia](docs/METRICS.md) | Jakość, opóźnienia, stan, przemieszczanie pamięci i pełny koszt. |
| [Architektura](docs/ARCHITECTURE.md) · [Model danych](docs/DATA_MODEL.md) | Przepływ sterowania, granice zaufania i niezmienne zapisy. |
| [Katalog idei](docs/IDEA_CATALOG.md) · [Prior art](docs/PRIOR_ART.md) | Rodziny obliczeniowe, alternatywy i kontekst naukowy. |
| [Pierwotna wizja](docs/ORIGINAL_MANIFEST.md) · [Roadmapa](docs/ROADMAP.md) | Długoterminowa ambicja i historyczna mapa G0–G8. Roadmapa nie jest bieżącą kolejką. |
| [Bezpieczeństwo i autonomia](docs/SAFETY.md) · [Instrukcje agenta](AGENTS.md) | Uprawnienia, limity, STOP/PAUSE i ograniczenia dostępu do danych. |

## Wkład w projekt

Przydatne są audyty pomiarów, silniejsze kontrole klasyczne, poprawki odtwarzalności i precyzyjne pytania badawcze. Otwórz [issue](https://github.com/Jaqwilk/NEXTAI/issues) z pytaniem, oczekiwaną obserwacją i dowodami albo zaproponuj konkretny [pull request](https://github.com/Jaqwilk/NEXTAI/pulls).

Przed zmianą zachowania badań przeczytaj [AGENTS.md](AGENTS.md), [program.md](program.md) i [protokół naukowy](docs/SCIENTIFIC_PROTOCOL.md). Zachowaj stare plany, wyniki, archiwa źródeł i zużycie budżetu. Zmiana chronionych źródeł wymaga udokumentowanej migracji; nowe porównania naukowe wymagają prospektywnych kontraktów.

<details>
<summary><strong>Granice wykonania i odtwarzalności</strong></summary>

- Pliki `STOP` lub `PAUSE` w katalogu głównym, aktywne blokady i tryb maintenance ograniczają wykonywanie eksperymentów.
- Pliki WT 8–9 pozostają poza zatwierdzonym zakresem dostępu.
- Audyt importów i osobne procesy zakładają współpracujący kod; nie są pełnym sandboxem systemowym.
- Lokalnie widoczne dane developerskie nie stanowią niezależnie ślepego holdoutu.
- Odtworzenie historycznych badań może wymagać lokalnych danych, dokładnych ocenianych źródeł oraz zapisanego sprzętu i oprogramowania.
- Harmonogram aplikacji jest osobny od dokumentacji repozytorium. Edycja README nie uruchamia cyklu badawczego.

</details>

---

<p align="center">
  <strong>Dowody przed architekturą.</strong><br>
  <sub>Każda zachowana idea powinna przetrwać test zaprojektowany tak, by ją obalić.</sub>
</p>
