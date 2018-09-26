"""
Tests of features described in Druckmann et. al. 2013 (https://academic.oup.com/cercor/article/23/12/2994/470476)

AP analysis details (from suplementary info): https://github.com/scidash/neuronunit/files/2295064/bhs290supp.pdf

Numbers in class names refer to the numbers in the publication table
"""

import quantities as q

import neuronunit.capabilities.spike_functions as sf
from .base import np, pq, ncap, VmTest, scores

none_score = {
                'mean': None,
                'std': None,
                'n': 0
             }

class Druckman2013AP:

    def __init__(self, waveform, threshold_time):
        self.waveform = waveform
        self.threshold_time = threshold_time
        self.wave_start_time = threshold_time - waveform.times[-1] / 2

        self.beginning_threshold = 12.0 # mV/ms

        self.waveform.t_start = 0*pq.ms

    def get_beginning(self):
        """
        The beginning of a spike was then determined by a crossing of a threshold on the derivative of the voltage (12mV/msec).

        :return: the voltage and time of the AP beginning
        """
        # Compute the discrete difference of the vm
        dvdt = np.array(np.diff(self.waveform, axis=0)) * pq.mV / self.waveform.sampling_period

        # Get the first time it crosses the threshold
        dvdt_over_th_first = np.where(dvdt > self.beginning_threshold)[0][0]

        begining_time = self.wave_start_time + self.waveform.times[dvdt_over_th_first]
        beginning_voltage = self.waveform[dvdt_over_th_first]

        return beginning_voltage, begining_time

    def get_end(self):
        """
        The end of the spike was determined by the minimum value of the afterhyperpolarization (AHP) following the spike.

        :return: The voltage and time at the AP end
        """

        return self.get_trough()

    def get_amplitude(self):
        """
        The amplitude of a spike is given by the difference between the voltage at the beginning and peak of the spike.

        :return: the amplitude value
        """
        v_begin, _ = self.get_beginning()
        v_peak, _ = self.get_peak()

        return (v_peak - v_begin)

    def get_halfwidth(self):
        """
        Amount of time in between the first crossing (in the upwards direction) of the
        half-height voltage value and the second crossing (in the downwards direction) of
        this value, for the first AP. Half-height voltage is the voltage at the beginning
        of the AP plus half the AP amplitude.

        :return:
        """
        v_begin, _ = self.get_beginning()
        amp = self.get_amplitude()
        half_v = v_begin + amp / 2.0

        above_half_v = np.where(self.waveform.magnitude > half_v)[0]

        half_start = self.waveform.times[above_half_v[0]]
        half_end = self.waveform.times[above_half_v[-1]]

        return half_end - half_start


    def get_peak(self):
        """
        The peak point of the spike is the maximum in between the beginning and the end.

        :return: the voltage and time of the peak
        """
        value = self.waveform.max()
        time = self.wave_start_time + self.waveform.times[np.where(self.waveform.magnitude == value)[0]]

        return value, time

    def get_trough(self):
        value = self.waveform.min()
        time = self.wave_start_time + self.waveform.times[np.where(self.waveform.magnitude == value)[0]]

        return value, time

class Druckmann2013Test(VmTest):
    """
    All tests inheriting from this class assume that the subject model:
     1. Was at steady state before time 0
     2. Starting at t=0, had a 2s step current injected into soma
    """
    required_capabilities = (ncap.ProducesActionPotentials,)
    score_type = scores.ZScore

    def __init__(self, **params):
        super(Druckmann2013Test, self).__init__(**params)

        self.params = {
            'injected_square_current': {
                'delay': 0 * pq.ms,
                'duration': 2 * pq.s,
                'amplitude': 0 * pq.pA
            },
            'threshold': -20 * pq.mV,
            'ap_window': 10 * pq.ms,
        }

        self.APs = None

    def current_length(self):
        return self.params['injected_square_current']['duration']

    def get_APs(self, model):
        """
        Spikes were detected by a crossing of a voltage threshold (-20 mV).

        :param model: model which provides the waveform to analyse
        :return: a list of Druckman2013APs
        """
        vm = model.get_membrane_potential()

        waveforms = sf.get_spike_waveforms(
            vm,
            threshold=self.params['threshold'],
            width=self.params['ap_window']
        )

        times = sf.get_spike_train(vm, self.params['threshold'])

        # Pass in the AP waveforms and the times when they occured
        self.APs = []
        for i in range(waveforms.shape[1]):
            self.APs.append(Druckman2013AP(waveforms[:,i], times[i]))

        return self.APs

class AP12AmplitudeDropTest(Druckmann2013Test):
    """
    1. Drop in AP amplitude (amp.) from first to second spike (mV)

    Difference in the voltage value between the amplitude of the first and second AP.

    Negative values indicate 2nd AP amplitude > 1st
    """

    name = "Drop in AP amplitude from 1st to 2nd AP"
    description = "Difference in the voltage value between the amplitude of the first and second AP"

    units = pq.mV

    def generate_prediction(self, model):
        aps = self.get_APs(model)

        if len(aps) >= 2:
            return {
                'mean': aps[0].get_amplitude() - aps[1].get_amplitude(),
                'std': 0,
                'n': 1
            }

        else:
            return none_score


class AP1SSAmplitudeChangeTest(Druckmann2013Test):
    """
    2. AP amplitude change from first spike to steady-state (mV)

    Steady state AP amplitude is calculated as the mean amplitude of the set of APs
    that occurred during the latter third of the current step.
    """

    name = "AP amplitude change from 1st AP to steady-state"
    description = """Steady state AP amplitude is calculated as the mean amplitude of the set of APs
    that occurred during the latter third of the current step."""

    units = pq.mV

    def generate_prediction(self, model):
        current_start = self.params['injected_square_current']['delay']

        start_latter_3rd = current_start + self.current_length() * 2.0 / 3.0
        end_latter_3rd = current_start + self.current_length()

        aps = self.get_APs(model)
        amps = np.array([ap.get_amplitude() for ap in aps])
        ap_times = np.array([ap.get_beginning()[1] for ap in aps])

        ss_amps = amps[np.where(
            (ap_times >= start_latter_3rd) &
            (ap_times <= end_latter_3rd))]

        if len(ss_amps) > 0:
            return {
                'mean': ss_amps.mean() * pq.mV,
                'std': ss_amps.std() * pq.mV,
                'n': len(ss_amps)
            }

        else:
            return none_score

class AP1AmplitudeTest(Druckmann2013Test):
    """
    3. AP 1 amplitude (mV)

    Amplitude of the first AP.
    """

    name = "First AP amplitude"
    description = "Amplitude of the first AP"

    units = pq.mV

    def generate_prediction(self, model, ap_index=0):
        aps = self.get_APs(model)

        if len(aps) > ap_index:
            return {
                'mean': aps[ap_index].get_amplitude(),
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class AP1WidthHalfHeightTest(Druckmann2013Test):
    """
    4. AP 1 width at half height (ms)
    """

    name = "First AP width at its half height"
    description = """Amount of time in between the first crossing (in the upwards direction) of the
    half-height voltage value and the second crossing (in the downwards direction) of
    this value, for the first AP. Half-height voltage is the voltage at the beginning of
    the AP plus half the AP amplitude."""

    units = pq.ms

    def generate_prediction(self, model, ap_index=0):
        aps = self.get_APs(model)

        if len(aps) > ap_index:
            return {
                'mean': aps[ap_index].get_halfwidth(),
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class AP1WidthPeakToTroughTest(Druckmann2013Test):
    """
    5. AP 1 peak to trough time (ms)

    Amount of time between the peak of the first AP and the trough, i.e., the
    minimum of the AHP.
    """

    name = "AP 1 peak to trough time"
    description = """Amount of time between the peak of the first AP and the trough, i.e., the minimum of the AHP"""

    units = pq.ms

    def generate_prediction(self, model, ap_index=0):
        aps = self.get_APs(model)

        if len(aps) > ap_index:
            ap = aps[ap_index]

            _, peak_t = ap.get_peak()
            _, trough_t = ap.get_trough()

            width = trough_t - peak_t

            return {
                'mean': width,
                'std': 0,
                'n': 1
            }

        else:
            return none_score


class AP1RateOfChangePeakToTroughTest(Druckmann2013Test):
    """
    6. AP 1 peak to trough rate of change (mV/ms)

    Difference in voltage value between peak and trough divided by the amount of time in
    between the peak and trough.
    """

    name = "AP 1 peak to trough rate of change"
    description = """Difference in voltage value between peak and trough over the amount of time in between the peak and trough."""

    units = pq.mV/pq.ms

    def generate_prediction(self, model, ap_index=0):
        aps = self.get_APs(model)

        if len(aps) > ap_index:
            ap = aps[ap_index]

            peak_v,   peak_t   = ap.get_peak()
            trough_v, trough_t = ap.get_trough()

            change = (trough_v - peak_v) / (trough_t - peak_t)

            return {
                'mean': change,
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class AP1AHPDepthTest(Druckmann2013Test):
    """
    7. AP 1 Fast AHP depth (mV)

    Difference between the minimum of voltage at the trough and the voltage value at
    the beginning of the AP.
    """

    name = "AP 1 Fast AHP depth"
    description = """Difference between the minimum of voltage at the trough and the voltage value at
    the beginning of the AP."""

    units = pq.mV

    def generate_prediction(self, model, ap_index=0):
        aps = self.get_APs(model)

        if len(aps) > ap_index:
            ap = aps[ap_index]

            begin_v,   _ = ap.get_beginning()
            trough_v, _  = ap.get_trough()

            change = begin_v - trough_v

            return {
                'mean': change,
                'std': 0,
                'n': 1
            }

        else:
            return none_score



class AP2AmplitudeTest(AP1AmplitudeTest):
    """
    8. AP 2 amplitude (mV)

    Same as :any:`AP1AmplitudeTest` but for second AP
    """

    name = "AP 2 amplitude"
    description = """Same as :any:`AP1AmplitudeTest` but for second AP"""

    def generate_prediction(self, model):
        return super(AP2AmplitudeTest, self).generate_prediction(model, ap_index=1)

class AP2WidthHalfHeightTest(AP1WidthHalfHeightTest):
    """
    9. AP 2 width at half height (ms)

    Same as :any:`AP1WidthHalfHeightTest` but for second AP
    """

    name = "AP 2 width at half height"
    description = """Same as :any:`AP1WidthHalfHeightTest` but for second AP"""

    def generate_prediction(self, model):
        return super(AP2WidthHalfHeightTest, self).generate_prediction(model, ap_index=1)

class AP2WidthPeakToTroughTest(AP1WidthPeakToTroughTest):
    """
    10. AP 2 peak to trough time (ms)

    Same as :any:`AP1WidthPeakToTroughTest` but for second AP
    """

    name = "AP 2 peak to trough time"
    description = """Same as :any:`AP1WidthPeakToTroughTest` but for second AP"""

    def generate_prediction(self, model):
        return super(AP2WidthPeakToTroughTest, self).generate_prediction(model, ap_index=1)

class AP2RateOfChangePeakToTroughTest(AP1RateOfChangePeakToTroughTest):
    """
    11. AP 2 peak to trough rate of change (mV/ms)

    Same as :any:`AP1RateOfChangePeakToTroughTest` but for second AP
    """

    name = "AP 2 peak to trough rate of change"
    description = """Same as :any:`AP1RateOfChangePeakToTroughTest` but for second AP"""

    def generate_prediction(self, model):
        return super(AP2RateOfChangePeakToTroughTest, self).generate_prediction(model, ap_index=1)

class AP2AHPDepthTest(AP1AHPDepthTest):
    """
    12. AP 2 Fast AHP depth (mV)

    Same as :any:`AP1AHPDepthTest` but for second AP
    """

    name = "AP 2 Fast AHP depth"
    description = """Same as :any:`AP1AHPDepthTest` but for second AP"""

    def generate_prediction(self, model):
        return super(AP2AHPDepthTest, self).generate_prediction(model, ap_index=1)

class AP12AmplitudeChangePercentTest(Druckmann2013Test):
    """
    13.	Percent change in AP amplitude, first to second spike (%)

    Difference in AP amplitude between first and second AP divided by the first AP
    amplitude.
    """

    name = "Percent change in AP amplitude, first to second spike "
    description = """Difference in AP amplitude between first and second AP divided by the first AP
    amplitude."""

    units = pq.dimensionless

    def generate_prediction(self, model):
        aps = self.get_APs(model)

        if len(aps) >= 2:

            amp1 = AP1AmplitudeTest().generate_prediction(model)["mean"]
            amp2 = AP2AmplitudeTest().generate_prediction(model)["mean"]

            change = (amp2-amp1)/amp1 * 100.0;

            return {
                'mean': change,
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class AP12HalfWidthChangePercentTest(Druckmann2013Test):
    """
    14. Percent change in AP width at half height, first to second spike (%)

    Difference in AP width at half-height between first and second AP divided by the
    first AP width at half-height.
    """

    name = "Percent change in AP width at half height, first to second spike"
    description = """Difference in AP width at half-height between first and second AP divided by the
    first AP width at half-height."""

    units = pq.dimensionless

    def generate_prediction(self, model):
        aps = self.get_APs(model)

        if len(aps) >= 2:

            width1 = AP1WidthHalfHeightTest().generate_prediction(model)["mean"]
            width2 = AP2WidthHalfHeightTest().generate_prediction(model)["mean"]

            change = (width2-width1)/width1 * 100.0;

            return {
                'mean': change,
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class AP12RateOfChangePeakToTroughPercentChangeTest(Druckmann2013Test):
    """
    15. Percent change in AP peak to trough rate of change, first to second spike (%)

    Difference in peak to trough rate of change between first and second AP divided
    by the first AP peak to trough rate of change.
    """

    name = "Percent change in AP peak to trough rate of change, first to second spike"
    description = """Difference in peak to trough rate of change between first and second AP divided
    by the first AP peak to trough rate of change."""

    units = pq.dimensionless

    def generate_prediction(self, model):
        aps = self.get_APs(model)

        if len(aps) >= 2:

            roc1 = AP1RateOfChangePeakToTroughTest().generate_prediction(model)["mean"]
            roc2 = AP2RateOfChangePeakToTroughTest().generate_prediction(model)["mean"]

            change = (roc2-roc1)/roc1 * 100.0;

            return {
                'mean': change,
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class AP12AHPDepthPercentChangeTest(Druckmann2013Test):
    """
    16 	Percent change in AP fast AHP depth, first to second spike (%)

    Difference in depth of fast AHP between first and second AP divided by the first
    AP depth of fast AHP.
    """

    name = "Percent change in AP fast AHP depth, first to second spike"
    description = """Difference in depth of fast AHP between first and second AP divided by the first
    AP depth of fast AHP."""

    units = pq.dimensionless

    def generate_prediction(self, model):
        aps = self.get_APs(model)

        if len(aps) >= 2:

            ap1 = AP1AHPDepthTest().generate_prediction(model)["mean"]
            ap2 = AP2AHPDepthTest().generate_prediction(model)["mean"]

            change = (ap2-ap1)/ap1 * 100.0;

            return {
                'mean': change,
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class InputResistanceTest(Druckmann2013Test):
    """
    17 	Input resistance for steady-state current (Ohm)

    Input resistance calculated by injecting weak subthreshold hyperpolarizing and
    depolarizing step currents. Input resistance was taken as linear fit of current to
    voltage difference.
    """

    name = "Input resistance for steady-state current"
    description = """Input resistance calculated by injecting weak subthreshold hyperpolarizing and
    depolarizing step currents. Input resistance was taken as linear fit of current to
    voltage difference"""

    units = pq.dimensionless

    def __init__(self, injection_currents=np.array([])*pq.nA, **params):
        super(InputResistanceTest, self).__init__(**params)

        if not injection_currents or len(injection_currents) < 2:
            raise Exception("Test requires at least two current injections")

        for i in injection_currents:
            if i.units != pq.nA:
                raise Exception("Injection current must be specified in nanoamps (nA)")

        self.injection_currents = injection_currents

    def generate_prediction(self, model):
        voltages = []

        # Loop through the injection currents
        for i in self.injection_currents:

            # Set the current amplitude
            self.params['injected_square_current']['amplitude'] = i

            # Inject current
            model.inject_square_current(self.params['injected_square_current'])

            # Get the voltage waveform
            vm = model.get_membrane_potential()

            # The voltage at final 1ms of current step is assumed to be steady state
            ss_voltage = np.median(vm.magnitude[np.where((vm.times >= 999*pq.ms) & (vm.times <= 1000*pq.ms))]) * pq.mV

            voltages.append(ss_voltage)

        # Rescale units
        amps = [i.rescale('A') for i in self.injection_currents]
        volts = [v.rescale('V') for v in voltages]



        # v = ir -> r is slope of v(i) curve
        slope, _ = np.polyfit(amps, volts, 1)
        slope *= pq.Ohm

        return {
            'mean': slope,
            'std': 0,
            'n': 1
        }



class AP1DelayMeanTest(Druckmann2013Test):
    """
    18 	Average delay to AP 1 (ms)

    Mean of the delay to beginning of first AP over experimental repetitions of step
    currents.
    """

class AP1DelaySDTest(Druckmann2013Test):
    """
    19 	SD of delay to AP 1 (ms)

    Standard deviation of the delay to beginning of first AP over experimental
    repetitions of step currents.
    """

class AP2DelayMeanTest(Druckmann2013Test):
    """
    20 	Average delay to AP 2 (ms)

    Same as :any:`AP1DelayMeanTest` but for 2nd AP
    """

class AP2DelaySDTest(Druckmann2013Test):
    """
    21 	SD of delay to AP 2 (ms)

    Same as :any:`AP1DelaySDTest` but for 2nd AP

    Only stochastic models will have a non-zero value for this test
    """

class Burst1ISIMeanTest(Druckmann2013Test):
    """
    22 	Average initial burst interval (ms)

    Initial burst interval is defined as the average of the first two ISIs, i.e., the average
    of the time differences between the first and second AP and the second and third
    AP. This feature is the average the initial burst interval across experimental
    repetitions.
    """

class Burst1ISISDTest(Druckmann2013Test):
    """
    23 	SD of average initial burst interval (ms)

    The standard deviation of the initial burst interval across experimental repetitions.
    """

class AccommodationMeanInitialTest(Druckmann2013Test):
    """
    24 	Average initial accommodation (%)

    Initial accommodation is defined as the percent difference between the spiking rate of the
    first fifth of the step current and the *third* fifth of the step current.
    """


class AccommodationMeanSSTest(Druckmann2013Test):
    """
    25 	Average steady-state accommodation (%)

    Steady-state accommodation is defined as the percent difference between the spiking rate
    of the first fifth of the step current and the last *fifth* of the step current.
    """


class AccommodationRateToSSTest(Druckmann2013Test):
    """
    26 	Rate of accommodation to steady-state (1/ms)

    The percent difference between the spiking rate of the first fifth of the step current and
    final fifth of the step current divided by the time taken to first reach the rate of
    steady state accommodation.
    """

class AccommodationMeanAtSSTest(Druckmann2013Test):
    """
    27 	Average accommodation at steady-state (%)

    Accommodation analysis based on a fit of the ISIs to an exponential function:
    ISI = A+B*exp(-t/tau). This feature gives the relative size of the constant term (A) to
    the term before the exponent (B).
    """

class AccommodationRateMeanAtSSTest(Druckmann2013Test):
    """
    28 	Average rate of accommodation during steady-state

    Accommodation analysis based on a fit of the ISIs to an exponential function.
    This feature is the time constant of the exponent.
    """

class ISICVTest(Druckmann2013Test):
    """
    29 	Average inter-spike interval (ISI) coefficient of variation (CV) (unit less)

    Coefficient of variation (mean divided by standard deviation) of the distribution
    of ISIs.
    """

class ISIMedianTest(Druckmann2013Test):
    """
    30 	Median of the distribution of ISIs (ms)

    Median of the distribution of ISIs.
    """

class ISIBurstMeanChangeTest(Druckmann2013Test):
    """
    31 	Average change in ISIs during a burst (%)

    Difference between the first and second ISI divided by the value of the first ISI.
    """

class SpikeRateStrongStimTest(Druckmann2013Test):
    """
    32 	Average rate, strong stimulus (Hz)

    Firing rate of strong stimulus.
    """

class AP1DelayMeanStrongStimTest(Druckmann2013Test):
    """
    33 	Average delay to AP 1, strong stimulus (ms)

    Same as :any:`AP1DelayMeanTest` but for strong stimulus
    """

class AP1DelaySDStrongStimTest(Druckmann2013Test):
    """
    34 	SD of delay to AP 1, strong stimulus (ms)

    Same as :any:`AP1DelaySDTest` but for strong stimulus
    """

class AP2DelayMeanStrongStimTest(Druckmann2013Test):
    """
    35 	Average delay to AP 2, strong stimulus (ms)


    Same as :any:`AP2DelayMeanTest` but for strong stimulus
    """

class AP2DelaySDStrongStimTest(Druckmann2013Test):
    """
    36 	SD of delay to AP 2, strong stimulus (ms)

    Same as :any:`AP2DelaySDTest` but for strong stimulus
    """

class Burst1ISIMeanStrongStimTest(Druckmann2013Test):
    """
    37 	Average initial burst ISI, strong stimulus (ms)

    Same as :any:`Burst1ISIMeanTest` but for strong stimulus
    """

class Burst1ISISDStrongStimTest(Druckmann2013Test):
    """
    38 	SD of average initial burst ISI, strong stimulus (ms)

    Same as :any:`Burst1ISISDTest` but for strong stimulus
    """
