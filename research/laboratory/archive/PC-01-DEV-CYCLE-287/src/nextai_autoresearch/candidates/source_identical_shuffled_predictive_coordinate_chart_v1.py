from .predictive_coordinate_chart_core import PredictiveCoordinateChart


class Candidate(PredictiveCoordinateChart):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="shuffled")

