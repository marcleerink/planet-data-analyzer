import multiprocessing.pool

class ReportProcess(multiprocessing.Process):
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


class ReportContext(type(multiprocessing.get_context())):
    Process = ReportProcess


class ReportPool(multiprocessing.pool.Pool):
    def __init__(self, *args, **kwargs):
        kwargs['context'] = ReportContext()
        super(ReportPool, self).__init__(*args, **kwargs)


