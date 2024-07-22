import multiprocessing

import numpy as np


class SharedNumpyArray:
    """A class for creating and managing shared numpy arrays across multiple processes.

    This class provides a way to create a numpy array that can be shared between
    different processes using multiprocessing.RawArray as the underlying storage.
    """

    def __init__(self, shape: tuple[int, ...], dtype: np.dtype = np.uint8) -> None:
        """Initialize a SharedNumpyArray.

        Args:
        ----
            shape (tuple[int, ...]): The shape of the numpy array.
            dtype (np.dtype, optional): The data type of the array. Defaults to np.uint8.

        """
        self.shape = shape
        self.dtype = dtype
        size = int(np.prod(shape))
        self.shared_array = multiprocessing.RawArray("B", size)

    def get_array(self) -> np.ndarray:
        """Get a numpy array view of the shared memory.

        Returns
        -------
            np.ndarray: A numpy array that shares memory with the underlying RawArray.

        """
        return np.frombuffer(self.shared_array, dtype=self.dtype).reshape(self.shape)
