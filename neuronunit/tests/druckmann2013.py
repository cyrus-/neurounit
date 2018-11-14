"""
Tests of features described in Druckmann et. al. 2013 (https://academic.oup.com/cercor/article/23/12/2994/470476)

AP analysis details (from suplementary info): https://github.com/scidash/neuronunit/files/2295064/bhs290supp.pdf

Numbers in class names refer to the numbers in the publication table
"""

import neuronunit.capabilities.spike_functions as sf
from .base import np, pq, ncap, VmTest, scores
from scipy.optimize import curve_fit
from elephant.spike_train_generation import threshold_detection
from neo import AnalogSignal

per_ms = pq.UnitQuantity('per_ms',1.0/pq.ms,symbol='per_ms')

none_score = {
                'mean': None,
                'std': None,
                'n': 0
             }

debug = True

class Druckmann2013AP:
    """
    This is a helper class that computes/finds aspects of APs as defined in Druckmann 2013
    """

    def __init__(self, waveform, begin_time):
        self.waveform = waveform
        self.begin_time = begin_time

        self.begin_time.units = pq.ms

    def get_beginning(self):
        """
        The beginning of a spike was then determined by a crossing of a threshold on the derivative of the voltage (12mV/msec).

        :return: the voltage and time of the AP beginning
        """
        begining_time = self.begin_time
        beginning_voltage = self.waveform[0]

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

        half_width = half_end - half_start
        half_width.units = pq.ms

        return half_width


    def get_peak(self):
        """
        The peak point of the spike is the maximum in between the beginning and the end.

        :return: the voltage and time of the peak
        """
        value = self.waveform.max()
        time = self.begin_time + self.waveform.times[np.where(self.waveform.magnitude == value)[0]]
        time.units = pq.ms

        return value, time

    def get_trough(self):
        value = self.waveform.min()
        time = self.begin_time + self.waveform.times[np.where(self.waveform.magnitude == value)[0]]
        time.units = pq.ms

        return value, time

class Druckmann2013Test(VmTest):
    """
    All tests inheriting from this class assume that the subject model:
     1. Is at steady state at time 0 (i.e. resume from SS)
     2. Starting at t=0, will have a 2s step current injected into soma, at least once
    """
    required_capabilities = (ncap.ProducesActionPotentials,)
    score_type = scores.ZScore

    def __init__(self, current_amplitude, **params):
        super(Druckmann2013Test, self).__init__(**params)

        self.params = {
            'injected_square_current': {
                'delay': 1000 * pq.ms,
                'duration': 2000 * pq.ms,
                'amplitude': current_amplitude
            },
            'threshold': -20 * pq.mV,
            'beginning_threshold': 12.0 * pq.mV/pq.ms,
            'ap_window': 10 * pq.ms,
            'repetitions': 1,
        }

        # This will be an array that stores DruckmannAPs
        self.APs = None

    def generate_prediction(self, model):
        results = []

        reps = self.params['repetitions']

        for rep in range(reps):
            pred = self.generate_repetition_prediction(model)
            results.append(pred)

        if reps > 1:
            return self.aggregate_repetitions(results)
        else:
            return results[0]

    def generate_repetition_prediction(self, model):
        raise NotImplementedError()

    def aggregate_repetitions(self, results):
        values = [rep['mean'] for rep in results]

        units = values[0].units if len(values) > 0 else self.units

        return {
            'mean': np.mean(values) * units,
            'std': np.std(values) * units,
            'n': len(results)
        }

    def current_length(self):
        return self.params['injected_square_current']['duration']

    def get_APs(self, model):
        """
        Spikes were detected by a crossing of a voltage threshold (-20 mV).

        :param model: model which provides the waveform to analyse
        :return: a list of Druckman2013APs
        """
        vm = model.get_membrane_potential()

        dvdt = np.array(np.diff(vm, axis=0)) * pq.mV / vm.sampling_period
        dvdt = AnalogSignal(dvdt, sampling_period=vm.sampling_period)

        threshold_crosses = threshold_detection(vm,threshold=self.params['threshold'])
        dvdt_threshold_crosses = threshold_detection(dvdt,threshold=self.params['beginning_threshold'])

        ap_beginnings = []
        for t in threshold_crosses:
            closest_beginning = dvdt_threshold_crosses[np.where(dvdt_threshold_crosses < t)][-1]
            closest_beginning.units = pq.ms
            ap_beginnings.append(closest_beginning)

        ap_waveforms = []
        for i, b in enumerate(ap_beginnings):
            if i != len(ap_beginnings)-1:
                waveform = vm.magnitude[np.where((vm.times >= b) & (vm.times < ap_beginnings[i + 1]))]
            else:
                waveform = vm.magnitude[np.where((vm.times >= b) & (vm.times < b + 100.0*pq.ms))]

            waveform = AnalogSignal(waveform, units=vm.units, sampling_rate=vm.sampling_rate)

            ap_waveforms.append(waveform)

        # Pass in the AP waveforms and the times when they occured
        self.APs = []
        for i, b in enumerate(ap_beginnings):
            self.APs.append(Druckmann2013AP(ap_waveforms[i], ap_beginnings[i]))

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
        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) >= 2:

            if debug:
                from matplotlib import pyplot as plt
                plt.plot(aps[0].waveform)
                plt.plot(aps[1].waveform)
                plt.show()

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
        model.inject_square_current(self.params['injected_square_current'])

        current_start = self.params['injected_square_current']['delay']

        start_latter_3rd = current_start + self.current_length() * 2.0 / 3.0
        end_latter_3rd = current_start + self.current_length()

        aps = self.get_APs(model)
        amps = np.array([ap.get_amplitude() for ap in aps]) * pq.mV
        ap_times = np.array([ap.get_beginning()[1] for ap in aps]) * pq.ms

        ss_aps = np.where(
            (ap_times >= start_latter_3rd) &
            (ap_times <= end_latter_3rd))

        ss_amps = amps[ss_aps]

        if len(aps) > 0 and len(ss_amps[0]) > 0:

            if debug:
                from matplotlib import pyplot as plt
                plt.plot(aps[0].waveform)
                for i in ss_aps[0]:
                    plt.plot(aps[i].waveform)
                plt.show()

            return {
                'mean': amps[0] - ss_amps.mean(),
                'std': ss_amps.std(),
                'n': len(ss_amps)
            }

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

        model.inject_square_current(self.params['injected_square_current'])

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

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) > ap_index:

            return {
                'mean': aps[ap_index].get_halfwidth(),
                'std': 0,
                'n': 1
            }

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

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) > ap_index:
            ap = aps[ap_index]

            _, peak_t = ap.get_peak()
            _, trough_t = ap.get_trough()

            width = trough_t - peak_t

            if debug:
                from matplotlib import pyplot as plt
                plt.plot(aps[0].waveform)
                plt.xlim(0, 1000)
                plt.show()

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

        model.inject_square_current(self.params['injected_square_current'])

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

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) > ap_index:
            ap = aps[ap_index]

            begin_v,   _ = ap.get_beginning()
            trough_v, _  = ap.get_trough()

            change = begin_v - trough_v


            if debug:
                from matplotlib import pyplot as plt
                plt.plot(aps[0].waveform)
                plt.xlim(0, 1000)
                plt.show()

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

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) >= 2:

            amp = self.params['injected_square_current']['amplitude']

            amp1 = AP1AmplitudeTest(amp).generate_prediction(model)["mean"]
            amp2 = AP2AmplitudeTest(amp).generate_prediction(model)["mean"]

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

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) >= 2:

            amp = self.params['injected_square_current']['amplitude']

            width1 = AP1WidthHalfHeightTest(amp).generate_prediction(model)["mean"]
            width2 = AP2WidthHalfHeightTest(amp).generate_prediction(model)["mean"]

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

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) >= 2:

            amp = self.params['injected_square_current']['amplitude']

            roc1 = AP1RateOfChangePeakToTroughTest(amp).generate_prediction(model)["mean"]
            roc2 = AP2RateOfChangePeakToTroughTest(amp).generate_prediction(model)["mean"]

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

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) >= 2:

            amp = self.params['injected_square_current']['amplitude']

            ap1 = AP1AHPDepthTest(amp).generate_prediction(model)["mean"]
            ap2 = AP2AHPDepthTest(amp).generate_prediction(model)["mean"]

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
    17 	Input resistance for steady-state current (MOhm)

    Input resistance calculated by injecting weak subthreshold hyperpolarizing and
    depolarizing step currents. Input resistance was taken as linear fit of current to
    voltage difference.
    """

    name = "Input resistance for steady-state current"
    description = """Input resistance calculated by injecting weak subthreshold hyperpolarizing and
    depolarizing step currents. Input resistance was taken as linear fit of current to
    voltage difference"""

    units = pq.Quantity(1,'MOhm')

    def __init__(self, injection_currents=np.array([])*pq.nA, **params):
        super(InputResistanceTest, self).__init__(current_amplitude=None, **params)

        if not injection_currents or len(injection_currents) < 2:
            raise Exception("Test requires at least two current injections")

        for i in injection_currents:
            if i.units != pq.nA:
                i.units = pq.nA

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
            ss_voltage = np.median(vm.magnitude[np.where((vm.times >= 1999*pq.ms) & (vm.times <= 2000*pq.ms))]) * pq.mV

            voltages.append(ss_voltage)

            if debug:
                from matplotlib import pyplot as plt
                plt.plot(vm)

        if debug:
            plt.show()

        # Rescale units
        amps = [i.rescale('A') for i in self.injection_currents]
        volts = [v.rescale('V') for v in voltages]

        # v = ir -> r is slope of v(i) curve
        slope, _ = np.polyfit(amps, volts, 1)
        slope *= pq.Ohm
        slope.units = pq.Quantity(1,'MOhm')

        if debug:
            from matplotlib import pyplot as plt
            plt.plot(amps, volts)
            plt.show()

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

    name = "First AP delay mean"
    description = "Mean delay to the first AP"

    units = pq.ms

    def __init__(self, current_amplitude, repetitions=7, **params):
        super(AP1DelayMeanTest, self).__init__(current_amplitude, **params)

        self.params['repetitions'] = repetitions

    def generate_repetition_prediction(self, model, ap_index=0):

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) > ap_index:
            delay = self.params['injected_square_current']['delay']

            if debug:
                from matplotlib import pyplot as plt
                vm = model.get_membrane_potential()
                plt.plot(vm.times.magnitude, vm.magnitude)
                plt.xlim(1, aps[ap_index].get_beginning()[1].rescale('sec').magnitude + 0.1)
                plt.show()

            return {
                'mean': aps[ap_index].get_beginning()[1] - delay,
                'std': 0,
                'n': 1
            }

        return none_score

class AP1DelaySDTest(AP1DelayMeanTest):
    """
    19 	SD of delay to AP 1 (ms)

    Standard deviation of the delay to beginning of first AP over experimental
    repetitions of step currents.
    """

    name = "First AP delay standard deviation"
    description = "Standard deviation of delay to the first AP"

    units = pq.ms

    def aggregate_repetitions(self, results):
        return {
            'mean': np.std([rep['mean'] for rep in results]) * self.units,
            'std': 0 * self.units,
            'n': len(results)
        }

class AP2DelayMeanTest(AP1DelayMeanTest):
    """
    20 	Average delay to AP 2 (ms)

    Same as :any:`AP1DelayMeanTest` but for 2nd AP
    """

    name = "Second AP delay mean"
    description = "Mean of delay to the second AP"

    def generate_repetition_prediction(self, model, ap_index=0):
        return super(AP2DelayMeanTest, self).generate_repetition_prediction(model, ap_index=1)

class AP2DelaySDTest(AP1DelaySDTest):
    """
    21 	SD of delay to AP 2 (ms)

    Same as :any:`AP1DelaySDTest` but for 2nd AP

    Only stochastic models will have a non-zero value for this test
    """

    name = "Second AP delay standard deviation"
    description = "Standard deviation of delay to the second AP"

    def generate_repetition_prediction(self, model, ap_index=0):
        return super(AP2DelaySDTest, self).generate_repetition_prediction(model, ap_index=1)

class Burst1ISIMeanTest(Druckmann2013Test):
    """
    22 	Average initial burst interval (ms)

    Initial burst interval is defined as the average of the first two ISIs, i.e., the average
    of the time differences between the first and second AP and the second and third
    AP. This feature is the average the initial burst interval across experimental
    repetitions.
    """

    name = "Initial burst interval mean"
    description = "Mean of the initial burst interval"

    units = pq.ms

    def __init__(self, current_amplitude, repetitions=7, **params):
        super(Burst1ISIMeanTest, self).__init__(current_amplitude, **params)

        self.params['repetitions'] = repetitions

    def generate_repetition_prediction(self, model):

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        if len(aps) >= 3:
            t1 = aps[0].get_beginning()[1]
            t2 = aps[1].get_beginning()[1]
            t3 = aps[2].get_beginning()[1]

            isi1 = t2 - t1
            isi2 = t3 - t2

            if debug:
                print("first 3 aps: %s, %s, %s"%(t1,t2,t3))
                print("2 isis: %s, %s" % (isi1, isi2))

            return {
                'mean': (isi1 + isi2) / 2.0,
                'std': 0,
                'n': 1
            }

        return none_score

class Burst1ISISDTest(Burst1ISIMeanTest):
    """
    23 	SD of average initial burst interval (ms)

    The standard deviation of the initial burst interval across experimental repetitions.
    """

    name = "Initial burst interval std"
    description = "StDev of the initial burst interval"

    def aggregate_repetitions(self, results):
        return {
            'mean': np.std([rep['mean'] for rep in results]) * self.units,
            'std': 0 * self.units,
            'n': len(results)
        }

class InitialAccommodationMeanTest(Druckmann2013Test):
    """
    24 	Average initial accommodation (%)

    Initial accommodation is defined as the percent difference between the spiking rate of the
    *first* fifth of the step current and the *third* fifth of the step current.
    """

    name = "Initial accomodation mean"
    description = "Mean of the initial accomodation"

    units = pq.dimensionless

    def generate_prediction(self, model):

        model.inject_square_current(self.params['injected_square_current'])

        current_start = self.params['injected_square_current']['delay']

        start_1st_5th = current_start
        end_1st_5th   = current_start + self.current_length() * 1/5.0

        start_3rd_5th = current_start + self.current_length() * 2/5.0
        end_3rd_5th   = current_start + self.current_length() * 3/5.0

        aps = self.get_APs(model)
        ap_times = np.array([ap.get_beginning()[1] for ap in aps])

        ap_count15 = np.where((ap_times >= start_1st_5th) & (ap_times <= end_1st_5th))[0]
        ap_count35 = np.where((ap_times >= start_3rd_5th) & (ap_times <= end_3rd_5th))[0]

        if debug:
            print("aps in 1st 5th: %s" % (len(ap_count15)))
            print("aps in 3rd 5th: %s" % (len(ap_count35)))

        if len(ap_count15) > 0:
            percent_diff = (len(ap_count35) - len(ap_count15)) / float(len(ap_count15)) * 100.0

            return {
                'mean': percent_diff,
                'std': 0,
                'n': 1
            }

        return none_score

class SSAccommodationMeanTest(Druckmann2013Test):
    """
    25 	Average steady-state accommodation (%)

    Steady-state accommodation is defined as the percent difference between the spiking rate
    of the *first* fifth of the step current and the *last* fifth of the step current.
    """

    name = "Steady state accomodation mean"
    description = "Mean of the steady state accomodation"

    units = pq.dimensionless

    def generate_prediction(self, model):

        model.inject_square_current(self.params['injected_square_current'])

        current_start = self.params['injected_square_current']['delay']

        start_1st_5th = current_start
        end_1st_5th   = current_start + self.current_length() * 1/5.0

        start_last_5th = current_start + self.current_length() * 4/5.0
        end_last_5th   = current_start + self.current_length()

        aps = self.get_APs(model)
        ap_times = np.array([ap.get_beginning()[1] for ap in aps])

        ap_count15 = np.where((ap_times >= start_1st_5th)  & (ap_times <= end_1st_5th))[0]
        ap_count55 = np.where((ap_times >= start_last_5th) & (ap_times <= end_last_5th))[0]

        if len(ap_count15) > 0:
            percent_diff = (len(ap_count55) - len(ap_count15)) / float(len(ap_count15)) * 100.0

            if debug:
                print("aps in 1st 5th: %s" % (len(ap_count15)))
                print("aps in last 5th: %s" % (len(ap_count55)))

            return {
                'mean': percent_diff,
                'std': 0,
                'n': 1
            }

        return none_score


class AccommodationRateToSSTest(Druckmann2013Test):
    """
    26 	Rate of accommodation to steady-state (percent/ms)

    The percent difference between the spiking rate of the *first* fifth of the step current and
    *final* fifth of the step current divided by the time taken to first reach the rate of
    steady state accommodation.

    Note: It's not clear what is meant by "time taken to first reach the rate of steady state
    accommodation". Here, it's computed as smallest t of an ISI which is longer than 0.95 of the
    mean ISIs in the final fifth of the current step.
    """

    name = "ISI Accomodation Rate"
    description = "Rate of ISI Accomodation"

    units = per_ms

    def generate_prediction(self, model):

        model.inject_square_current(self.params['injected_square_current'])

        current_start = self.params['injected_square_current']['delay']

        start_1st_5th = current_start
        end_1st_5th   = current_start + self.current_length() * 1/5.0

        start_last_5th = current_start + self.current_length() * 4/5.0
        end_last_5th   = current_start + self.current_length()

        aps = self.get_APs(model)
        ap_times = np.array([ap.get_beginning()[1] for ap in aps])

        aps_15 = np.where((ap_times >= start_1st_5th)  & (ap_times <= end_1st_5th))[0]
        aps_55 = np.where((ap_times >= start_last_5th) & (ap_times <= end_last_5th))[0]

        if len(aps_15) > 0 and len(aps_55) > 2:
            percent_diff = (len(aps_55) - len(aps_15)) / float(len(aps_15)) * 100.0

            if debug:
                print("aps in 1st 5th vs last 5th, percent change: %s" % (percent_diff))

            isis = np.diff(ap_times)
            isi_times = ap_times[1:]

            isis_55 = isis[np.where((isi_times >= start_last_5th) & (isi_times <= end_last_5th))]

            ss_isi = np.mean(isis_55)

            if debug:
                print("mean ISI at SS: %s" % (ss_isi))

            nearly_ss_isis = np.where(isis >= 0.95*ss_isi)[0]

            if len(nearly_ss_isis) > 0:

                first_nearly_ss_isi_time = isi_times[nearly_ss_isis[0]] * pq.ms

                if debug:
                    print("time of first nearly mean SS ISI: %s" % (first_nearly_ss_isi_time))

                if first_nearly_ss_isi_time > 0:
                    return {
                        'mean': percent_diff / (first_nearly_ss_isi_time - self.params['injected_square_current']['delay']),
                        'std': 0,
                        'n': 1
                    }

        return none_score

class AccommodationAtSSMeanTest(Druckmann2013Test):
    """
    27 	Average accommodation at steady-state (%)

    Accommodation analysis based on a fit of the ISIs to an exponential function:
    ISI = A+B*exp(-t/tau). This feature gives the relative size of the constant term (A) to
    the term before the exponent (B).
    """

    name = "ISI Steady state accomodation mean"
    description = "Mean of the ISI steady state accomodation"

    units = pq.dimensionless

    def generate_prediction(self, model):

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)
        ap_times = np.array([ap.get_beginning()[1] for ap in aps])

        isis = np.diff(ap_times)
        isi_delays = ap_times[1:] - self.params['injected_square_current']['delay'].rescale('ms').magnitude
        isi_delays = isi_delays - isi_delays[0]

        if len(isis) >= 2:

            def isi_func(t, A, B, tau):
                return A + B * np.exp(-t/(1.0*tau))

            from lmfit import Model

            model = Model(isi_func)
            params = model.make_params(A=isis[-1], B=-1.0, tau=10.0)
            params['A'].min = 0
            params['B'].max = 0
            params['tau'].min = 0

            result = model.fit(isis, t=isi_delays, params=params)

            [A, tau, B] = result.best_values.values()

            if debug:
                from matplotlib import pyplot as plt
                print(result.fit_report())

                plt.plot(isi_delays, isis, 'bo')
                plt.plot(isi_delays, result.best_fit, 'r-')
                plt.show()

            return {
                'mean': self.get_final_result(A, B, tau),
                'std': 0,
                'n': 1
            }

        else:
            return none_score

    def get_final_result(self, A, B, tau):
        return B / float(A) * 100.0

class AccommodationRateMeanAtSSTest(AccommodationAtSSMeanTest):
    """
    28 	Average rate of accommodation during steady-state

    Accommodation analysis based on a fit of the ISIs to an exponential function.
    This feature is the time constant (tau) of the exponent.
    """

    name = "ISI accomodation time constant"
    description = "Time constant of the ISI accomodation"

    units = pq.ms

    def get_final_result(self, A, B, tau):
        return tau * pq.ms

class ISICVTest(Druckmann2013Test):
    """
    29 	Average inter-spike interval (ISI) coefficient of variation (CV) (unit less)

    Coefficient of variation (mean divided by standard deviation) of the distribution
    of ISIs.
    """

    name = "ISI CV"
    description = "ISI Coefficient of Variation"

    units = pq.dimensionless

    def generate_prediction(self, model):

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)
        ap_times = np.array([ap.get_beginning()[1] for ap in aps])

        isis = np.diff(ap_times)

        if len(isis) >= 2:

            return {
                'mean': np.mean(isis) / np.std(isis),
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class ISIMedianTest(Druckmann2013Test):
    """
    30 	Median of the distribution of ISIs (ms)

    Median of the distribution of ISIs.
    """

    name = "ISI Median"
    description = "ISI Median"

    units = pq.ms

    def generate_prediction(self, model):

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)
        ap_times = np.array([ap.get_beginning()[1] for ap in aps])

        isis = np.diff(ap_times)

        if len(isis) >= 1:

            return {
                'mean': np.median(isis),
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class ISIBurstMeanChangeTest(Druckmann2013Test):
    """
    31 	Average change in ISIs during a burst (%)

    Difference between the first and second ISI divided by the value of the first ISI.
    """

    name = "ISI Burst Mean Change"
    description = "ISI Burst Mean Change"

    units = pq.dimensionless

    def generate_prediction(self, model):

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)
        ap_times = np.array([ap.get_beginning()[1] for ap in aps])

        isis = np.diff(ap_times)

        if len(isis) >= 2:

            return {
                'mean': (isis[1] - isis[0])/isis[0] * 100.0,
                'std': 0,
                'n': 1
            }

        else:
            return none_score

class SpikeRateStrongStimTest(Druckmann2013Test):
    """
    32 	Average rate, strong stimulus (Hz)

    Firing rate of strong stimulus.
    """

    name = "Strong Stimulus Firing Rate"
    description = "Strong Stimulus Firing Rate"

    units = pq.Hz

    def generate_prediction(self, model):

        model.inject_square_current(self.params['injected_square_current'])

        aps = self.get_APs(model)

        duration = self.current_length()

        spike_rate = len(aps) / duration
        spike_rate.units = pq.Hz

        return {
            'mean': spike_rate,
            'std': 0,
            'n': 1
        }

class AP1DelayMeanStrongStimTest(AP1DelayMeanTest):
    """
    33 	Average delay to AP 1, strong stimulus (ms)

    Same as :any:`AP1DelayMeanTest` but for strong stimulus
    """

class AP1DelaySDStrongStimTest(AP1DelaySDTest):
    """
    34 	SD of delay to AP 1, strong stimulus (ms)

    Same as :any:`AP1DelaySDTest` but for strong stimulus
    """

class AP2DelayMeanStrongStimTest(AP2DelayMeanTest):
    """
    35 	Average delay to AP 2, strong stimulus (ms)


    Same as :any:`AP2DelayMeanTest` but for strong stimulus
    """

class AP2DelaySDStrongStimTest(AP2DelaySDTest):
    """
    36 	SD of delay to AP 2, strong stimulus (ms)

    Same as :any:`AP2DelaySDTest` but for strong stimulus
    """

class Burst1ISIMeanStrongStimTest(Burst1ISIMeanTest):
    """
    37 	Average initial burst ISI, strong stimulus (ms)

    Same as :any:`Burst1ISIMeanTest` but for strong stimulus
    """

class Burst1ISISDStrongStimTest(Burst1ISISDTest):
    """
    38 	SD of average initial burst ISI, strong stimulus (ms)

    Same as :any:`Burst1ISISDTest` but for strong stimulus
    """