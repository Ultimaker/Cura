from UM.Signal import Signal, SignalEmitter
class HttpUploadDataStream(SignalEmitter):
    def __init__(self):
        super().__init__()
        self._data_list = []
        self._total_length = 0
        self._read_position = 0

    progressSignal = Signal()

    def write(self, data):
        data = bytes(data,'UTF-8')
        size = len(data)
        if size < 1:
            return
        blocks = int(size / 2048)
        for n in range(0, blocks):
            self._data_list.append(data[n*2048:n*2048+2048])
        self._data_list.append(data[blocks*2048:])
        self._total_length += size

    def read(self, size):
        if self._read_position >= len(self._data_list):
            return None
        ret = self._data_list[self._read_position]
        self._read_position += 1

        self.progressSignal.emit(float(self._read_position) / float(len(self._data_list)))
        return ret

    def __len__(self):
        return self._total_length