# Aktualny stan NEXTAI

Aktualny autoryzowany pakiet to `AUDIT-REPAIR-20261002-V1`: naprawa ustaleń
audytu, testy na oddzielnym klonie Git oraz jeden nowy eksperyment kalibracyjny
`mutable_contact_ledger_v2`. Zgoda i prospektywny kontrakt znajdują się w
`research/laboratory/AUDIT-REPAIR-20261002-V1.json` oraz
`research/plans/AUDIT-REPAIR-20261002-V1.json`.

Zweryfikowaną kolejkę i zużycie uprawnień wyznacza `uv run nextai lab status`.
Ten dokument jest opisem, nie dodatkową zgodą. Do chwili gotowości evaluatora
obowiązuje maintenance; potem dokładnie jedna rejestracja i jeden losowy seed,
bez retry. Wynik kończy etap na `AUDIT-REPAIR-DECISION`.

Stare etapy PC-01, WT-01, REVIEW-01 i MUC v1 pozostają zakończone. Nie zwiększamy
ich budżetów. Dane WT 8–9, harmonogram, zewnętrzne modele/API i mechanizm
delta-memory są poza zakresem. Zachowujemy wszystkie wyniki, porażki i źródła.

MUC v1 ma negatywną kontrolę uczoną i wadliwe koszty oraz etykiety pomiaru.
Nowa kohorta ma odrębną tożsamość; jej wyników nie łączymy z v1. Uczone role v2
to jawne czytniki par tekstowych z iteracyjną kompozycją, nie pełne autoregresyjne
LLM. Kalibracja nie ustanawia nowej architektury ani przewagi ekonomicznej.
