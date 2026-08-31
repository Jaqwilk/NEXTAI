# `program_library_adversarial_v2`

## Zmiana względem v1

Extractor, DSL, enumerator, sposób liczenia operacji i wszystkie kandydatury pozostają niezmienione. Zmienia się tylko rozkład danych:

- połowa rozwiązanych programów zawiera prawdziwy fragment `(0, 1)` dwa razy;
- połowa jest nieistotna i zawiera konkurencyjne częste fragmenty, lecz nie `(0, 1)`;
- zadania held-out używają prawdziwego fragmentu naprzemiennie raz albo dwa razy;
- screen obejmuje trzy seedy, K=`8,32,128`, D=`1,4,6,8` i 12 zadań na komórkę.

To atakuje trzy słabości EXP-0007: jeden seed, czysty korpus i gwarantowane dwukrotne reuse.

## Kryterium

Na poziomie seed×K learned extractor powinien wybierać `(0, 1)`. Koszt discovery jest doliczany przez `fit_ops`, korpus przez `state_bytes`, a koszt na zadanie przez `amortized_cold_ops`. D=1 pozostaje kontrolą bez możliwości użycia makra. Oracle i mismatch oddzielają poprawną abstrakcję od samego rozszerzenia gramatyki.

Wyniki v1 i v2 są osobnymi kohortami. Pozytywny screen nie usuwa ograniczeń ręcznego DSL, znanej długości programu ani widocznego benchmarku.
