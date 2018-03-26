"""Dynamic neuronunit tests, e.g. investigating dynamical systems properties"""


from elephant.statistics import isi
from elephant.statistics import cv
from elephant.statistics import lv
from neuronunit.capabilities.channel import *
from .base import np, pq, cap, VmTest, scores, AMPL, DELAY, DURATION
from .waveform import InjectedCurrentAPWidthTest
from .fi import RheobaseTestP, RheobaseTest


class TFRTypeTest(RheobaseTest):
    """Tests whether a model has particular threshold firing rate dynamics,
    i.e. type 1 or type 2."""

    name = "Firing Rate Type test"

    description = (("A test of the instantaneous firing rate dynamics, i.e. "
                    "type 1 or type 2"))

    score_type = scores.BooleanScore

    def __init__(self, *args, **kwargs):
        super(TFRTypeTest,self).__init__(*args,**kwargs)
        if self.name == self.__class__.name:
            self.name = "Firing Rate Type %d test" % self.observation['type']

    def validate_observation(self, observation):
        super(TFRTypeTest,self).validate_observation(observation,
                                                     united_keys=['rheobase'],
                                                     nonunited_keys=['type'])
        assert ('type' in observation) and (observation['type'] in [1,2]), \
            ("observation['type'] must be either 1 or 2, corresponding to "
             "type 1 or type 2 threshold firing rate dynamics.")

    def generate_prediction(self, model):
        """Implementation of sciunit.Test.generate_prediction."""

        model.rerun = True
        if 'rheobase' in self.observation:
            guess = self.observation['rheobase']
        else:
            guess = 100.0*pq.pA
        lookup = self.threshold_FI(model, self.units, guess=guess)
        sub = np.array([x for x in lookup if lookup[x]==0])*self.units
        supra = np.array([x for x in lookup if lookup[x]>0])*self.units
        if self.verbose:
            if len(sub):
                print("Highest subthreshold current is %s" \
                      % float(sub.max().round(2)))
            else:
                print("No subthreshold current was tested.")
            if len(supra):
                print("Lowest suprathreshold current is %s" \
                      % supra.min().round(2))
            else:
                print("No suprathreshold current was tested.")

        prediction = None
        if len(sub) and len(supra):
            supra = np.array([x for x in lookup if lookup[x]>0]) # No units
            thresh_i = supra.min()
            n_spikes_at_thresh = lookup[thresh_i]
            if n_spikes_at_thresh == 1:
                prediction = 1 # Type 1 dynamics.
            elif n_spikes_at_thresh > 1:
                prediction = 2 # Type 2 dynamics.

        return prediction

    def compute_score(self, observation, prediction):
        """Implementation of sciunit.Test.score_prediction."""
        #print("%s: Observation = %s, Prediction = %s" % \
        #    (self.name,str(observation),str(prediction)))
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type(prediction == observation)
        return score


class BurstinessTest(InjectedCurrentAPWidthTest):
    """Tests whether a model exhibits the observed burstiness"""

    def __init__(self, observation={'cv_mean':None,'cv_std':None},
                 name=None,
                 params=None):
        pass

    name = "Burstiness test"

    description = (("A test of AP bursting at the provided current"))

    score_type = scores.RatioScore

    units = pq.dimensionless

    cv_threshold = 1.0

    def validate_observation(self, observation):
        super(TFRTypeTest,self).validate_observation(observation,
                                                     nonunited_keys=['cv'])

    def generate_prediction(self, model):
        model.inject_square_current(observation['current'])
        spike_train = model.get_spike_train()
        if len(spike_train) >= 3:
            cv(spike_train)*pq.dimensionless
            #isis = isi(spike_train)
            #cv_old = np.std(isis) / np.mean(isis)
        else:
            cv = None
        return {'cv':cv}

    def compute_score(self, observation, prediction):
        """Implementation of sciunit.Test.score_prediction."""
        #print("%s: Observation = %s, Prediction = %s" % \
        #    (self.name,str(observation),str(prediction)))
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type.compute(observation,prediction,key='cv')
        return score

class CVTest(VmTest):
    """Tests whether a model exhibits the observed burstiness"""

    def __init__(self, observation={'cv_mean':None,'cv_std':None},
                 name=None,
                 params=None):
        pass

    name = "Coefficient of Variation Test"
    description = (("For neurons and muscle cells check the Coefficient of Variation on a list of Interval Between Spikes given a spike train recording."))

    score_type = scores.RatioScore
    units = pq.dimensionless

    def __init__(self, *args, **kwargs):
        super(CVTest,self).__init__(*args,**kwargs)

        if self.name == self.__class__.name:
            self.name = "Firing Rate Type %d test" % self.observation['type']

    def validate_observation(self,observation):
        pass
    #def validate_observation(self, observation):
    #    super(CVTest,self).validate_observation(observation,
    #                                                 united_keys=['cv'],
    #                                                 nonunited_keys=['type'])
        #assert ('type' in observation) and (observation['type'] in [1,2]), \
        #    ("observation['type'] must be either 1 or 2, corresponding to "
        #     "type 1 or type 2 threshold firing rate dynamics.")


    def generate_prediction(self, model = None):
        st = model.get_spike_train()
        #prediction = abs(cv(st))
        prediction = {}
        prediction['cv'] = abs(cv(st))*pq.dimensionless
        prediction['mean'] = abs(cv(st))*pq.dimensionless
        return prediction

    def compute_score(self, observation, prediction):
        """Implementation of sciunit.Test.score_prediction."""

        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type.compute(observation,prediction,key='cv')
        return score


class ISITest(VmTest):
    """Tests whether a model exhibits the observed Inter Spike Intervals"""

    def __init__(self, observation={'isi_mean':None,'isi_std':None},
                 name=None,
                 params=None):
        pass


    name = "Inter Spike Interval Tests"
    description = (("For neurons and muscle cells check the mean Interval Between Spikes given a spike train recording."))
    score_type = scores.RatioScore
    units = pq.ms

    def __init__(self, *args, **kwargs):
        super(ISITest,self).__init__(*args,**kwargs)

        if self.name == self.__class__.name:
            self.name = "Inter Spike Interval Test %d test" % self.observation['type']


    def generate_prediction(self, model = None):
        prediction = {}
        st = model.get_spike_train()
        isis = isi(st)
        prediction['isi'] = float(np.mean(isis))*1000.0*pq.ms
        return prediction

    def compute_score(self, observation, prediction):
        """Implementation of sciunit.Test.score_prediction."""
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            print(observation,prediction)
            score = self.score_type.compute(observation,prediction,key='isi')
        return score

class FiringRateTest(RheobaseTest):
    """Tests whether a model exhibits the observed burstiness"""

    def __init__(self, observation={'sps_mean':None,'sps_std':None},
                 name=None,
                 params=None):
        pass

    name = "Firing Rate Test"
    description = (("Spikes Per Second."))
    score_type = scores.RatioScore
    units = pq.dimensionless

    def __init__(self, *args, **kwargs):
        super(LocalVariationTest,self).__init__(*args,**kwargs)
        if self.name == self.__class__.name:
            self.name = "Firing Rate Type %d test" % self.observation['type']

    '''
    def validate_observation(self, observation):
        super(LocalVariationTest,self).validate_observation(observation,
                                                     united_keys=['rheobase'],
                                                     nonunited_keys=['type'])

        assert ('type' in observation) and (observation['type'] in [1,2]), \
            ("observation['type'] must be either 1 or 2, corresponding to "
             "type 1 or type 2 threshold firing rate dynamics.")
    '''

    def generate_prediction(self, model = None):
        """Implementation of sciunit.Test.generate_prediction."""

        ass = model.get_membrane_potential()
        spike_count = model.get_spike_count()

        window = ass.t_stop-ass.t_start
        prediction['sps_mean'] = float(spike_count/window)
        # prediction should be number of spikes divided by time.
        return predicted_rate



    def compute_score(self, observation, prediction):
        """Implementation of sciunit.Test.score_prediction."""
        #print("%s: Observation = %s, Prediction = %s" % \
        #    (self.name,str(observation),str(prediction)))
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type.compute(observation,prediction,key='sps_mean')
        return score

class LocalVariationTest(VmTest):
    """Tests whether a model exhibits the observed burstiness"""

    def __init__(self, observation={'cv_mean':None,'cv_std':None},
                 name=None,
                 params=None):
        pass

    required_capabilities = (cap.ReceivesSquareCurrent,
                             cap.ProducesSpikes)

    name = "Local Variation test"
    description = (("For neurons and muscle cells with slower non firing dynamics like CElegans neurons check to see how much \
    varition is in the continuous membrane potential."))
    score_type = scores.RatioScore
    units = pq.dimensionless
    local_variation = 0.0 # 1.0

    def __init__(self, *args, **kwargs):
        super(LocalVariationTest,self).__init__(*args,**kwargs)
        if self.name == self.__class__.name:
            self.name = "Firing Rate Type %d test" % self.observation['type']



    def generate_prediction(self, model = None):
        prediction = lv(model.get_membrane_potential())
        return prediction

        return prediction




    def compute_score(self, observation, prediction):
        """Implementation of sciunit.Test.score_prediction."""
        #print("%s: Observation = %s, Prediction = %s" % \
        #    (self.name,str(observation),str(prediction)))
        if prediction is None:
            score = scores.InsufficientDataScore(None)
        else:
            score = self.score_type.compute(observation,prediction,key='lv')
        return score
