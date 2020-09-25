
from neuronunit.tests.base import np, pq, ncap, VmTest, scores, AMPL#, DELAY, DURATION
import quantities as qt
from neuronunit.tests.target_spike_current import SpikeCountSearch, SpikeCountRangeSearch

import efel

from sciunit import scores
def format_efel_tests(self,dtc,observed_spk_cnt):
    scs = SpikeCountSearch(observed_spk_cnt)
    model = dtc.dtc_to_model()
    ampl = scs.generate_prediction(model)

    for t in dtc.tests:
        t.observed_spk_cnt = observed_spk_cnt
        t.model = model
        t.ampl = ampl
    
    return tests
class AdaptionTest(VmTest):
    """Tests the input resistance of a cell.
    """
    score_type = scores.RatioScore
    def __init__(self,observation=None,observed_spk_cnt=None):
        self = self
        self.obervation = observation
        self.observed_spk_cnt = observed_spk_cnt
        scs = SpikeCountSearch(self.observed_spk_cnt)
        self.model = dtc.dtc_to_model()
        self.ampl = scs.generate_prediction(model)

    def generate_prediction(model):
        params = {'injected_square_current':
            {'amplitude':self.ampl, 'delay':100*pq.ms, 'duration':1000*pq.ms}}
        vm_used = self.model.inject_square_current(params)
        efel.setThreshold(0)

        trace3 = {'T': [float(t)*1000.0 for t in vm_used.times],
                  'V': [float(v) for v in vm_used.magnitude],
                  'stimulus_current': [current]}
        ALLEN_DURATION = 2000*qt.ms
        ALLEN_DELAY = 1000*qt.ms
        trace3['stim_end'] = [ float(ALLEN_DELAY)+float(ALLEN_DURATION) ]
        trace3['stim_start'] = [ float(ALLEN_DELAY)]
        results = efel.getMeanFeatureValues([trace3],['adaptation_index','adaptation_index2'])
        self.prediction = results
        return results
    def compute_score(self):
        if self.prediction is None:
            return None
        else:
            score = super(VmTest, self).compute_score(self.observation,
                                                                    self.prediction)
        score.related_data['vm'] = self.vm
        return score


class BaseVMTest(VmTest):
    score_type = scores.RatioScore

    def __init__(self,observation=None,observed_spk_cnt=None):
        self = self
        self.obervation = observation
        self.observed_spk_cnt = observed_spk_cnt
        scs = SpikeCountSearch(self.observed_spk_cnt)
        self.model = dtc.dtc_to_model()
        self.ampl = scs.generate_prediction(model)

    def generate_prediction(model):
        params = {'injected_square_current':
            {'amplitude':self.ampl, 'delay':100*pq.ms, 'duration':1000*pq.ms}}
        vm_used = self.model.inject_square_current(params)
        efel.setThreshold(0)

        trace3 = {'T': [float(t)*1000.0 for t in vm_used.times],
                  'V': [float(v) for v in vm_used.magnitude],
                  'stimulus_current': [current]}
        ALLEN_DURATION = 2000*qt.ms
        ALLEN_DELAY = 1000*qt.ms

        trace3['stim_end'] = [ float(ALLEN_DELAY)+float(ALLEN_DURATION) ]
        trace3['stim_start'] = [ float(ALLEN_DELAY)]
        results = efel.getMeanFeatureValues([trace3],['voltage_base'])
        self.prediction = results
        return results
    def compute_score(self):
        if self.prediction is None:
            return None
        else:
            score = super(VmTest, self).compute_score(self.observation,
                                                                    self.prediction)
        score.related_data['vm'] = self.vm
        return score

class SpikeHeightVMTest(VmTest):
    score_type = scores.RatioScore

    def __init__(self,observation=None,observed_spk_cnt=None):
        self = self
        self.obervation = observation
        self.observed_spk_cnt = observed_spk_cnt
        scs = SpikeCountSearch(self.observed_spk_cnt)
        self.model = dtc.dtc_to_model()
        self.ampl = scs.generate_prediction(model)

    def generate_prediction(model):
        params = {'injected_square_current':
            {'amplitude':self.ampl, 'delay':100*pq.ms, 'duration':1000*pq.ms}}
        vm_used = self.model.inject_square_current(params)
        efel.setThreshold(0)

        trace3 = {'T': [float(t)*1000.0 for t in vm_used.times],
                  'V': [float(v) for v in vm_used.magnitude],
                  'stimulus_current': [current]}
        ALLEN_DURATION = 2000*qt.ms
        ALLEN_DELAY = 1000*qt.ms

        trace3['stim_end'] = [ float(ALLEN_DELAY)+float(ALLEN_DURATION) ]
        trace3['stim_start'] = [ float(ALLEN_DELAY)]
        results = efel.getMeanFeatureValues([trace3],['mean_AP_amplitude'])
        self.prediction = results
        return results
    def compute_score(self):
        if self.prediction is None:
            return None
        else:
            score = super(VmTest, self).compute_score(self.observation,
                                                                    self.prediction)
        score.related_data['vm'] = self.vm
        return score
#simple_yes_list = ['mean_AP_amplitude','mean_frequency','min_AHP_values','min_voltage_between_spikes','minimum_voltage','all_ISI_values','ISI_log_slope','mean_frequency','adaptation_index2','first_isi','ISI_CV','median_isi','AHP_depth_abs','sag_ratio2','sag_ratio2','peak_voltage','voltage_base','Spikecount','ohmic_input_resistance_vb_ssse','ohmic_input_resistance']

class PeakSpikesHeightVMTest(VmTest):
    score_type = scores.RatioScore

    def __init__(self,observation=None,observed_spk_cnt=None):
        self = self
        self.obervation = observation
        self.observed_spk_cnt = observed_spk_cnt
        scs = SpikeCountSearch(self.observed_spk_cnt)
        self.model = dtc.dtc_to_model()
        self.ampl = scs.generate_prediction(model)

    def generate_prediction(model):
        params = {'injected_square_current':
            {'amplitude':self.ampl, 'delay':100*pq.ms, 'duration':1000*pq.ms}}
        vm_used = self.model.inject_square_current(params)
        efel.setThreshold(0)

        trace3 = {'T': [float(t)*1000.0 for t in vm_used.times],
                  'V': [float(v) for v in vm_used.magnitude],
                  'stimulus_current': [current]}
        ALLEN_DURATION = 2000*qt.ms
        ALLEN_DELAY = 1000*qt.ms

        trace3['stim_end'] = [ float(ALLEN_DELAY)+float(ALLEN_DURATION) ]
        trace3['stim_start'] = [ float(ALLEN_DELAY)]
        results = efel.getMeanFeatureValues([trace3],['peak_voltage'])
        self.prediction = results
        return results
    def compute_score(self):
        if self.prediction is None:
            return None
        else:
            score = super(VmTest, self).compute_score(self.observation,
                                                                    self.prediction)
        score.related_data['vm'] = self.vm
        return score

class sag_ratio2VMTest(VmTest):
    score_type = scores.RatioScore

    def __init__(self,observation=None,observed_spk_cnt=None):
        self = self
        self.obervation = observation
        self.observed_spk_cnt = observed_spk_cnt
        scs = SpikeCountSearch(self.observed_spk_cnt)
        self.model = dtc.dtc_to_model()
        self.ampl = scs.generate_prediction(model)

    def generate_prediction(model):
        params = {'injected_square_current':
            {'amplitude':self.ampl, 'delay':100*pq.ms, 'duration':1000*pq.ms}}
        vm_used = self.model.inject_square_current(params)
        efel.setThreshold(0)

        trace3 = {'T': [float(t)*1000.0 for t in vm_used.times],
                  'V': [float(v) for v in vm_used.magnitude],
                  'stimulus_current': [current]}
        ALLEN_DURATION = 2000*qt.ms
        ALLEN_DELAY = 1000*qt.ms

        trace3['stim_end'] = [ float(ALLEN_DELAY)+float(ALLEN_DURATION) ]
        trace3['stim_start'] = [ float(ALLEN_DELAY)]
        results = efel.getMeanFeatureValues([trace3],['sag_ratio2'])
        self.prediction = results
        return results
    def compute_score(self):
        if self.prediction is None:
            return None
        else:
            score = super(VmTest, self).compute_score(self.observation,
                                                                    self.prediction)
        score.related_data['vm'] = self.vm
        return score


class AHP_depth_abs(VmTest):
    score_type = scores.RatioScore

    def __init__(self,observation=None,observed_spk_cnt=None):
        self = self
        self.obervation = observation
        self.observed_spk_cnt = observed_spk_cnt
        scs = SpikeCountSearch(self.observed_spk_cnt)
        self.model = dtc.dtc_to_model()
        self.ampl = scs.generate_prediction(model)

    def generate_prediction(model):
        params = {'injected_square_current':
            {'amplitude':self.ampl, 'delay':100*pq.ms, 'duration':1000*pq.ms}}
        vm_used = self.model.inject_square_current(params)
        efel.setThreshold(0)

        trace3 = {'T': [float(t)*1000.0 for t in vm_used.times],
                  'V': [float(v) for v in vm_used.magnitude],
                  'stimulus_current': [current]}
        ALLEN_DURATION = 2000*qt.ms
        ALLEN_DELAY = 1000*qt.ms

        trace3['stim_end'] = [ float(ALLEN_DELAY)+float(ALLEN_DURATION) ]
        trace3['stim_start'] = [ float(ALLEN_DELAY)]
        results = efel.getMeanFeatureValues([trace3],['sag_ratio2'])
        self.prediction = results
        return results
    def compute_score(self):
        if self.prediction is None:
            return None
        else:
            score = super(VmTest, self).compute_score(self.observation,
                                                                    self.prediction)
        score.related_data['vm'] = self.vm
        return score
"""Dynamic neuronunit tests, e.g. investigating dynamical systems properties"""


from elephant.statistics import isi
from elephant.statistics import cv
from elephant.statistics import lv
from neuronunit.capabilities.channel import *
from .base import np, pq, ncap, VmTest, scores, AMPL, DELAY, DURATION
from .waveform import InjectedCurrentAPWidthTest
from .fi import RheobaseTest


class TFRTypeTest(RheobaseTest):
    """Test whether a model has particular threshold firing rate dynamics,
    i.e. type 1 or type 2."""

    def __init__(self, *args, **kwargs):
        super(TFRTypeTest, self).__init__(*args, **kwargs)
        if self.name == self.__class__.name:
            self.name = "Firing Rate Type %d test" % self.observation['type']

    name = "Firing Rate Type test"

    description = (("A test of the instantaneous firing rate dynamics, i.e. "
                    "type 1 or type 2"))

    score_type = scores.BooleanScore

    def validate_observation(self, observation):
        super(TFRTypeTest, self).validate_observation(observation,
                                                      united_keys=['rheobase'],
                                                      nonunited_keys=['type'])
        assert ('type' in observation) and (observation['type'] in [1, 2]), \
            ("observation['type'] must be either 1 or 2, corresponding to "
             "type 1 or type 2 threshold firing rate dynamics.")

    def generate_prediction(self, model):
        """Implement sciunit.Test.generate_prediction."""

        model.rerun = True
        if 'rheobase' in self.observation:
            guess = self.observation['rheobase']
        else:
            guess = 100.0*pq.pA
        lookup = self.threshold_FI(model, self.units, guess=guess)
        sub = np.array([x for x in lookup if lookup[x] == 0])*self.units
        supra = np.array([x for x in lookup if lookup[x] > 0])*self.units
        if self.verbose:
            if len(sub):
                print("Highest subthreshold current is %s"
                      % float(sub.max().round(2)))
            else:
                print("No subthreshold current was tested.")
            if len(supra):
                print("Lowest suprathreshold current is %s"
                      % supra.min().round(2))
            else:
                print("No suprathreshold current was tested.")

        prediction = None
        if len(sub) and len(supra):
            supra = np.array([x for x in lookup if lookup[x] > 0])  # No units
            thresh_i = supra.min()
            n_spikes_at_thresh = lookup[thresh_i]
            if n_spikes_at_thresh == 1:
                prediction = 1  # Type 1 dynamics.
            elif n_spikes_at_thresh > 1:
                prediction = 2  # Type 2 dynamics.

        return prediction

    def compute_score(self, observation, prediction):
        """Implement sciunit.Test.score_prediction."""
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type(prediction == observation)
        return score


class BurstinessTest(InjectedCurrentAPWidthTest):
    """Test whether a model exhibits the observed burstiness"""

    name = "Burstiness test"

    description = (("A test of AP bursting at the provided current"))

    score_type = scores.RatioScore

    units = pq.dimensionless

    nonunited_observation_keys = ['cv']

    cv_threshold = 1.0

    def generate_prediction(self, model):
        model.inject_square_current(self.run_params['current'])
        spike_train = model.get_spike_train()
        if len(spike_train) >= 3:
            value = cv(spike_train)*pq.dimensionless
        else:
            value = None
        return {'cv': value}

    def compute_score(self, observation, prediction):
        """Implement sciunit.Test.score_prediction."""
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type.compute(observation, prediction, key='cv')
        return score


class ISICVTest(VmTest):
    """Test whether a model exhibits the observed burstiness"""

    name = "ISI Coefficient of Variation Test"
    description = (("For neurons and muscle cells check the Coefficient of "
                    "Variation on a list of Interval Between Spikes given a "
                    "spike train recording."))
    score_type = scores.RatioScore
    units = pq.dimensionless
    united_observation_keys = []
    nonunited_observation_keys = ['cv']

    def generate_prediction(self, model=None):
        st = model.get_spike_train()
        if len(st) >= 3:
            value = abs(cv(st))*pq.dimensionless
        else:
            value = None
        prediction = {'cv': value}
        return prediction

    def compute_score(self, observation, prediction):
        """Implement sciunit.Test.score_prediction."""

        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            if self.verbose:
                print(observation, prediction)
            score = self.score_type.compute(observation, prediction, key='cv')
        return score


class ISITest(VmTest):
    """Test whether a model exhibits the observed Inter Spike Intervals"""

    def __init__(self, observation={'isi_mean': None, 'isi_std': None},
                 name=None,
                 params=None):
        pass

    name = "Inter Spike Interval Tests"
    description = (("For neurons and muscle cells check the mean Interval "
                    "Between Spikes given a spike train recording."))
    score_type = scores.ZScore
    units = pq.ms

    def __init__(self, *args, **kwargs):
        super(ISITest, self).__init__(*args, **kwargs)

        if self.name == self.__class__.name:
            self.name = "Inter Spike Interval Test %d test" % \
                        self.observation['type']

    def generate_prediction(self, model=None):
        st = model.get_spike_train()
        isis = isi(st)
        value = float(np.mean(isis))*1000.0*pq.ms
        prediction = {'value': alue}
        return prediction

    def compute_score(self, observation, prediction):
        """Implement sciunit.Test.score_prediction."""
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type.compute(observation, prediction)
        return score


class FiringRateTest(RheobaseTest):
    """Test whether a model exhibits the observed burstiness"""

    def __init__(self, *args, **kwargs):
        super(LocalVariationTest, self).__init__(*args, **kwargs)
        if self.name == self.__class__.name:
            self.name = "Firing Rate Type %d test" % self.observation['type']

    name = "Firing Rate Test"
    description = (("Spikes Per Second."))
    score_type = scores.RatioScore
    units = pq.dimensionless

    def generate_prediction(self, model=None):
        """Implements sciunit.Test.generate_prediction."""

        ass = model.get_membrane_potential()
        spike_count = model.get_spike_count()

        window = ass.t_stop-ass.t_start
        prediction = {'value': float(spike_count/window)}
        # prediction should be number of spikes divided by time.
        return prediction

    def compute_score(self, observation, prediction):
        """Implement sciunit.Test.score_prediction."""
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type.compute(observation, prediction,
                                            key='sps_mean')
        return score


class LocalVariationTest(VmTest):
    """Tests whether a model exhibits the observed burstiness"""

    def __init__(self, observation={'cv_mean': None, 'cv_std': None},
                 name=None,
                 params=None):
        pass

    required_capabilities = (ncap.ReceivesSquareCurrent,
                             ncap.ProducesSpikes)

    name = "Local Variation test"
    description = (("For neurons and muscle cells with slower non firing "
                    "dynamics like CElegans neurons check to see how much "
                    "variation is in the continuous membrane potential."))
    score_type = scores.RatioScore
    units = pq.dimensionless
    local_variation = 0.0  # 1.0

    def __init__(self, *args, **kwargs):
        super(LocalVariationTest, self).__init__(*args, **kwargs)
        if self.name == self.__class__.name:
            self.name = "Firing Rate Type %d test" % self.observation['type']

    def generate_prediction(self, model=None):
        prediction = lv(model.get_membrane_potential())
        return prediction

        return prediction

    def compute_score(self, observation, prediction):
        """Implementation of sciunit.Test.score_prediction."""
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type.compute(observation, prediction, key='lv')
        return score
