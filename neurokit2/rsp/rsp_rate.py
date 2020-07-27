# -*- coding: utf-8 -*-
import numpy as np

from ..signal import (signal_resample, signal_rate, signal_findpeaks, signal_interpolate,
                      signal_filter, signal_timefrequency, signal_period)
from .rsp_peaks import rsp_peaks


def rsp_rate(rsp_cleaned, peaks=None, sampling_rate=1000, window=10, hop_size=1, method="peak",
             peak_method="khodadad2018"):
    """Find respiration rate by cross-correlation method.
    Parameters
    ----------
    rsp_cleaned : Union[list, np.array, pd.Series]
        The cleaned respiration channel as returned by `rsp_clean()`.
    sampling_rate : int
        The sampling frequency of 'rsp_cleaned' (in Hz, i.e., samples/second).
    window : int
        The duration of the sliding window (in second). Default to 10 seconds.
    hop_size : int
        The number of samples between each successive window. Default to 1 sample.
    method : str
        Method can be either "peak" or "xcorr". In "peak" method, rsp_rate is calculated from the
        periods between respiration peaks. In "xcorr" method, cross-correlations between the changes
        in respiration with a bank of sinusoids of different frequencies are caclulated to indentify
        the principal frequency of oscillation.
    peak_method : str
        Method to identify respiration peaks. Can be one of "khodadad2018" (default) or "biosppy".

    Return
    ------
    rsp_rate : np.ndarray
        Instantenous respiration rate.

    Example
    -------
    >>> import neurokit2 as nk
    >>> rsp_signal = nk.data("rsp_200hz.txt").iloc[:,0]
    >>> sampling_rate=200
    >>> rsp_cleaned = nk.rsp_clean(rsp_signal)
    >>> rsp_rate_peak = nk.rsp_rate(rsp_cleaned, sampling_rate=sampling_rate, method="peaks")
    >>> rsp_rate_xcorr = nk.rsp_rate(rsp_cleaned, sampling_rate=sampling_rate, method="xcorr")
    """

    if method.lower() in ["peak", "peaks", "signal_rate"]:
        if peaks is None:
            peaks, info = rsp_peaks(rsp_cleaned, sampling_rate=sampling_rate, method=peak_method)
        rsp_rate = signal_rate(peaks, sampling_rate=sampling_rate, desired_length=len(rsp_cleaned), interpolation_method="linear")

    elif method.lower() in ["cross-correlation", "xcorr"]:
        rsp_rate = _rsp_rate_xcorr(rsp_cleaned, sampling_rate=sampling_rate,
                                   window=window, hop_size=hop_size)

    else:
        raise ValueError(
                "NeuroKit error: rsp_rate(): 'method' should be"
                " one of 'peak', or 'cross-correlation'."
                )

    return rsp_rate



# =============================================================================
# Cross-correlation method
# =============================================================================


def _rsp_rate_xcorr(rsp_cleaned, sampling_rate=1000, window=10, hop_size=1):

    N = len(rsp_cleaned)
    # Downsample data to 10Hz
    desired_sampling_rate = 10
    rsp = signal_resample(rsp_cleaned, sampling_rate=sampling_rate, desired_sampling_rate=desired_sampling_rate)

    # Define paramters
    window_length = int(desired_sampling_rate * window)

    rsp_rate = []
    for start in np.arange(0, N, hop_size):
        window_segment = rsp[start: start + window_length]
        if len(window_segment) < window_length:
            break # the last frames that are smaller than windlow_length
        # Calculate the 1-order difference
        diff = np.ediff1d(window_segment)
        norm_diff = diff / np.max(diff)
        # Find xcorr for all frequencies with diff
        xcorr = []
        t = np.linspace(0, window, len(diff))
        for frequency in np.arange(5/60, 30.25/60, 0.25/50):
            # Define the sin waves
            sin_wave = np.sin(2 * np.pi * frequency * t)
            # Calculate cross-correlation
            _xcorr = np.corrcoef(norm_diff, sin_wave)[0, 1]
            xcorr.append(_xcorr)

        # Find frequency with the highest xcorr with diff
        max_frequency_idx = np.argmax(xcorr)
        max_frequency = np.arange(5/60, 30.25/60, 0.25/60)[max_frequency_idx]
        # Append max_frequency to rsp_rate - instanteneous rate
        rsp_rate.append(max_frequency)

    x = np.arange(len(rsp_rate))
    y = rsp_rate
    rsp_rate = signal_interpolate(x, y, x_new=len(rsp_cleaned), method="linear")
    # Smoothing
    rsp_rate = signal_filter(rsp_rate, highcut=0.1, order=4, sampling_rate=sampling_rate)

    # Convert to Brpm
    rsp_rate = np.multiply(rsp_rate, 60)

    return np.array(rsp_rate)


#    plt.figure()
#    plt.subplot(211)
#    plt.plot(rsp_cleanedx)
#    plt.grid()
#    plt.title('Raw Data')
#    plt.subplot(212)
##    plt.title('Peak method')
#    plt.plot(rsp_ratex, label="peak")
#    plt.grid()
##    plt.subplot(213)
##    plt.title('xcorr method')
#    plt.plot(rsp_rate2x, label="tam")
##    plt.grid()
##    plt.subplot(414)
##    plt.title('xcorr_modified method')
#    plt.plot(rsp_rate3x, label="miso")
#    plt.legend()
##    plt.grid()
#    plt.xlabel('Time (Samples)')
#    plt.ylabel('Breath per Minute')
