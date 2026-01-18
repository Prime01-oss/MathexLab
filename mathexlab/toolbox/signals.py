import numpy as np
import scipy.signal
import scipy.fft
from mathexlab.math.arrays import MatlabArray

def fft(x, n=None, dim=-1):
    data = x._data if isinstance(x, MatlabArray) else x
    return MatlabArray(scipy.fft.fft(data, n=n, axis=dim))

def ifft(x, n=None, dim=-1):
    data = x._data if isinstance(x, MatlabArray) else x
    return MatlabArray(scipy.fft.ifft(data, n=n, axis=dim))

def fftshift(x, axes=None):
    data = x._data if isinstance(x, MatlabArray) else np.array(x)
    return MatlabArray(np.fft.fftshift(data, axes=axes))

def ifftshift(x, axes=None):
    data = x._data if isinstance(x, MatlabArray) else np.array(x)
    return MatlabArray(np.fft.ifftshift(data, axes=axes))

def spectrogram(x, window=None, noverlap=None, nfft=None, fs=1.0):
    x_data = np.asarray(x).flatten()
    if nfft is None: nfft = 256
    f, t, Sxx = scipy.signal.spectrogram(
        x_data, fs=fs, window=('hann' if window is None else window),
        nperseg=nfft, noverlap=noverlap
    )
    return MatlabArray(Sxx), MatlabArray(f), MatlabArray(t)

def pwelch(x, window='hann', noverlap=None, nfft=None, fs=1.0):
    x_data = np.asarray(x).flatten()
    if nfft is None: nfft = 256
    f, Pxx = scipy.signal.welch(
        x_data, fs=fs, window=window, 
        nperseg=nfft, noverlap=noverlap
    )
    return MatlabArray(Pxx), MatlabArray(f)

def findpeaks(data, **kwargs):
    x = np.asarray(data).flatten()
    if isinstance(data, MatlabArray):
        x = data._data.flatten()
    idxs, properties = scipy.signal.find_peaks(x, **kwargs)
    pks = x[idxs]
    return MatlabArray(pks), MatlabArray(idxs + 1)