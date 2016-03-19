from obspy.clients.fdsn import Client
from obspy import read


def _decompose_sncl(sncl, start, end):
    sncl_list = map(str.strip, sncl.split('.'))
    sncl_list = ['*' if len(x) == 0 else x for x in sncl_list]
    sncl_list.append(start)
    sncl_list.append(end)
    return tuple(sncl_list)


class DataServices:
    """

    """
    def __init__(self, client_url=None, local_data_path=None):
        """
        :param client_url: the url of the service to wrap
        :param local_data_path: a path to a local data file
        """

        self.client = Client(client_url)
        self.local_data_path = local_data_path

    def check_connection(self):
        pass

    def get_streams(self, sncl_list, start, end):
        """
        pares down the passed in sncl_list given availability
        :param sncl_list: sncl list to generate streams from
        :returns: a stream object
        """
        if self.client is not None:
            bulk = [_decompose_sncl(sncl, start, end) for sncl in sncl_list]
            return self.client.get_waveforms_bulk(bulk)
        else:
            return read(self.local_data_path)
