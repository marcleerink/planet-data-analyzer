import json

def geojson_import(aoi_file):
    with open(aoi_file) as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']


def api_json_writer(response, filepath):
    json_o = json.dumps(response, indent=4)
    with open(filepath, "w") as outfile:
        outfile.write(json_o)


# multiprocessing tool
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


