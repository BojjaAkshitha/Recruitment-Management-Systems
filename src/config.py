from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    seed: int = 20261022
    requisitions: int = 100
    candidates: int = 2000
    applications: int = 3000
    interviews: int = 600
    offers: int = 150
    output_dir: str = "data"
    inject_anomalies: bool = True
