import multiprocessing

import numpy as np


class SharedNumpyArray:
    def __init__(self, shape: tuple[int, ...], dtype: np.dtype = np.uint8) -> None:
        self.shape = shape
        self.dtype = dtype
        size = int(np.prod(shape))
        self.shared_array = multiprocessing.RawArray("B", size)

    def get_array(self) -> np.ndarray:
        return np.frombuffer(self.shared_array, dtype=self.dtype).reshape(self.shape)
