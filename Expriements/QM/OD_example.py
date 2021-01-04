
from pgc_macro_with_OD import pgc

pgc_experiment = pgc()

while True:
    pgc_experiment.MeasureOD(0.1)
