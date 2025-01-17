from .core_parameter import CoreParameter


class DiurnalCycleParameter(CoreParameter):
    def __init__(self):
        super(DiurnalCycleParameter, self).__init__()
        self.print_statements = False
        self.normalize_test_amp = False
        self.ref_timeseries_input = False
        self.test_timeseries_input = False
        self.normalize_amp_int = 0
