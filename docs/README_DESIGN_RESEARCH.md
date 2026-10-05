# README — analiza projektu i przegląd wzorców GitHub

Data: 5 października 2026. Zakres: prezentacja NEXTAI na GitHubie, bez nowego eksperymentu naukowego.

## Co przedstawia NEXTAI

Projekt jest lokalnym laboratorium do falsyfikowania hipotez o zasadach obliczeniowych AI. Cel to zdolność na jednostkę pełnego kosztu inferencji. Długoterminowa wizja następcy LLM pozostaje ambicją; obecne dowody nie uprawniają do przedstawiania repozytorium jako gotowej nowej architektury.

Przegląd struktury objął wszystkie 912 śledzonych modułów Python w `src/`: odczyt źródeł i analizę AST, łącznie 48 723 linii. W tym są 704 pliki w `candidates/` i 117 w `benchmarks/`; wiele to wersje, kontrole lub wrappery, a nie niezależne algorytmy. Sprawdzono także strukturę 156 modułów testowych, 192 planów JSON, 115 wyników JSON i 21 dokumentów w `docs/`. Liczby opisują rozmiar materiału, nie jakość dowodów. Archiwa historyczne potraktowano jako materiał do zachowania, bez uruchamiania ich kodu ani odczytu chronionych danych WT.

Szczegółowy przegląd semantyczny objął:

- [Aktualne instrukcje](../AGENTS.md), [program](../program.md), [stan](../research/state.json), [konfigurację](../config/research.toml) i zweryfikowany `nextai lab status`.
- [Pierwotną wizję](ORIGINAL_MANIFEST.md), [katalog idei](IDEA_CATALOG.md), [protokół](SCIENTIFIC_PROTOCOL.md), [metryki](METRICS.md), [architekturę](ARCHITECTURE.md), [model danych](DATA_MODEL.md), [bezpieczeństwo](SAFETY.md), [setup](CODEX_SETUP.md) i [raport](../research/REPORT.md).
- CLI, runner, granice audytu, kontrolę manifestu, certyfikat preflight, interfejs kandydatów, bootstrap, generator PVM, benchmark v5 i nadzór drzew procesów.
- Raporty [0005](../research/analyses/EXP-20261004-0005.md), [0006](../research/analyses/EXP-20261004-0006.md), [0007](../research/analyses/EXP-20261004-0007.md), [addendum 0008](../research/analyses/EXP-20261004-0008-ADDENDUM-V1.md) oraz [zamknięcie przygotowania](../research/analyses/PVM01-REPRO-PREPARATION-ADDENDUM-V1.md).

Nie wykonano pełnego audytu poprawności każdego historycznego algorytmu; analiza AST służyła inwentaryzacji, a szczegółowe czytanie — ustaleniu celu, architektury, ograniczeń i wiarygodnej treści README.

Poprzednie README przedstawiało etap AUDIT-REPAIR/MUC jako bieżący. Tymczasem stan po cyklu 311 wskazuje zakończone PVM v5, naprawę zgodności i aktywną kontynuację w maintenance. Nowe README oddziela stabilny opis projektu od datowanego przeglądu wyników i odsyła do CLI po bieżącą kolejkę.

## Metoda przeglądu innych repozytoriów

Przejrzano strony GitHub i oryginalne pliki README 17 popularnych projektów związanych z ML, agentami, narzędziami developerskimi i infrastrukturą. Liczby gwiazdek poniżej pochodzą z publicznego GitHub API podczas przeglądu; to migawka, nie stałe wartości. Analizowano początek strony, kolejność sekcji, grafiki, badge, szybki start, tabele, nawigację, dokumentację i ujawnianie ograniczeń.

Wnioski projektowe są interpretacją tych obserwacji. Popularność nie dowodzi, że konkretny układ README powoduje wzrost liczby gwiazdek. Nie kopiowano tekstów, logotypów ani grafik innych projektów.

| Repozytorium | Gwiazdki podczas przeglądu | Zaobserwowany wzorzec | Zastosowanie w NEXTAI |
| :--- | ---: | :--- | :--- |
| [Transformers](https://github.com/huggingface/transformers) | 166 957 | Centralny logotyp, wybór języka, instalacja i szybki start; osobno przydatność i ograniczenia. | Nagłówek, wersje EN/PL i jawny zakres projektu. |
| [PyTorch](https://github.com/pytorch/pytorch) | 103 759 | Mocna identyfikacja, krótkie określenie funkcji, czytelna dokumentacja możliwości. | Zwięzły opis laboratorium i tabela komponentów. |
| [vLLM](https://github.com/vllm-project/vllm) | 93 177 | Centralna marka, jednozdaniowe pozycjonowanie, pasek ważnych odnośników. | Slogan i nawigacja na początku strony. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | 130 314 | Szeroki baner, kompaktowe badge i szybki start blisko początku. | Własny baner SVG i cztery badge o sprawdzalnym znaczeniu. |
| [nanoGPT](https://github.com/karpathy/nanoGPT) | 63 549 | Wyrazista ilustracja i bezpośrednie objaśnienie celu, uruchomienia i baseline'ów. | Konkretny opis pytania i wyników z kontrolami. |
| [autoresearch](https://github.com/karpathy/autoresearch) | 97 281 | Wyjaśnienie idei, pętli pracy, struktury projektu i decyzji projektowych. | Schemat badania i mapa repozytorium. |
| [Ollama](https://github.com/ollama/ollama) | 182 201 | Rozpoznawalna marka, prosta obietnica i ścieżki startu według środowiska. | Czytelne wymagania i instalacja lokalna. |
| [uv](https://github.com/astral-sh/uv) | 90 409 | Krótka definicja, highlights, wizualizacja i przejście do dokumentacji. | Tabela możliwości i uporządkowana ścieżka czytania. |
| [FastAPI](https://github.com/fastapi/fastapi) | 102 808 | Centralny nagłówek, badge, proste przykłady i wyraźne linki do dokumentacji. | Spójny nagłówek i krótkie bloki poleceń. |
| [LangChain](https://github.com/langchain-ai/langchain) | 147 443 | Logotyp, krótkie pozycjonowanie, quickstart i mała sekcja zasobów. | Ograniczenie marketingowego wstępu, bezpośrednie zasoby. |
| [AutoGen](https://github.com/microsoft/autogen) | 61 261 | Widoczny status maintenance, instalacja, przykłady i wybór dalszej ścieżki. | Jawna różnica między aktywnym programem a nieaktywnym scoringiem. |
| [Ray](https://github.com/ray-project/ray) | 43 970 | Grupowanie bibliotek i zastosowań, instalacja i przewodnik po dokumentacji. | Grupowanie komponentów zamiast listy setek plików. |
| [MLflow](https://github.com/mlflow/mlflow) | 28 258 | Szybkie rozpoczęcie i sekcje uporządkowane według sposobu użycia. | Trzy kroki startu; osobno poznawanie projektu i wykonywanie badań. |
| [JAX](https://github.com/jax-ml/jax) | 36 377 | Prosty opis, spis treści, przykłady transformacji i jawne ograniczenia. | Jasne pytanie badawcze i rozwijane ograniczenia. |
| [nanochat](https://github.com/karpathy/nanochat) | 58 424 | Grafika, wyniki z kontekstem, setup, research i struktura plików. | Wyniki z zakresem twierdzenia oraz mapa kodu. |
| [DeepSpeed](https://github.com/deepspeedai/DeepSpeed) | 43 194 | Identyfikacja projektu, rozdzielone możliwości i ścieżki instalacji. | Wyraźne sekcje i wymagania środowiska. |
| [scikit-learn](https://github.com/scikit-learn/scikit-learn) | 67 472 | Rzeczowy opis biblioteki, sprawdzalne sygnały infrastruktury, instalacja i wkład. | Badge powiązane z rzeczywistą konfiguracją i konkretne propozycje wkładu. |

Dodatkowo sprawdzono [oficjalne wskazówki GitHub dotyczące README](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes), w szczególności opis celu, startu, odnośników względnych i automatycznej nawigacji według nagłówków.

## Decyzje dotyczące wyglądu i treści

1. **Własna identyfikacja.** Grafit, bursztyn, czytelna typografia i ścieżka przez rzadką sieć węzłów odnoszą się do pytania o koszt obliczeń. Grafika jest ilustracją idei, nie wynikiem pomiaru.
2. **Angielski punkt wejścia i pełna wersja polska.** Angielski ułatwia odbiór międzynarodowy; polski zachowuje wygodną ścieżkę dla właściciela projektu i obecnej dokumentacji. Obie wersje mają ten sam zakres faktów.
3. **Maksymalnie cztery badge.** Python i PyTorch wynikają z `pyproject.toml`; protokół v3 z konfiguracji; experimental określa etap. Brak badge fikcyjnego CI, coverage, licencji, pobrań czy opublikowanego pakietu.
4. **Instalacja przez istniejący bootstrap.** README wykorzystuje kontrolę budżetu dysku i przypięte zależności zamiast niezweryfikowanego instalatora lub polecenia treningowego.
5. **Wyniki z decyzjami i odnośnikami.** KEEP, DISCARD i INCONCLUSIVE są rozróżnione; zachowano dominację kontroli klasycznych i brak awansu architektury. Nie zbudowano wykresu łączącego różne kohorty.
6. **Dokumentacja jako przewodnik.** Tabele kierują do konkretnych źródeł; ważne szczegóły są rozwijane. Nie przenoszono całej wieloetapowej historii do README.
7. **Opis GitHub.** Krótki opis laboratorium i trafne tematy uzupełniają prezentację repozytorium. Nie dodano fikcyjnej witryny, społeczności, sponsorów ani afiliacji.

## Migracja chronionego README

README jest plikiem chronionym przez manifest. Prośba użytkownika bezpośrednio autoryzuje jego przebudowę i publikację w istniejącym repozytorium. Niniejsza notatka dokumentuje cel i granice zmiany przed odświeżeniem manifestu.

Zakres migracji: README, polskie tłumaczenie, dwie grafiki SVG i niniejsza notatka. Istniejący mechanizm `integrity freeze --overwrite` archiwizuje poprzedni manifest przed utworzeniem bieżącego. Istniejący mechanizm preflight archiwizuje poprzedni certyfikat. Oczekiwana zmiana w zestawie chronionych plików dotyczy wyłącznie `README.md`; candidate bundle, kod wykonawczy, konfiguracja, metryki, bramki, historyczne wyniki i limity pozostają zachowane.

Migracja prezentacji nie aktywuje nowej kohorty naukowej, scoringu, rejestracji, fitu, danych ani harmonogramu. Poprzednie wyniki wskazują swoje historyczne źródła i nie są przeliczane. Weryfikacja obejmuje odnośniki i kotwice, render GitHub, SVG, integralność, `doctor`, `lab status` i porównanie surowych hashy dotychczasowych plików. Szczegóły techniczne i wynik weryfikacji zapisuje osobny receipt migracji.
