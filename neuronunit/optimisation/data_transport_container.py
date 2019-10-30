import numpy as np
#from neuronunit.optimisation.optimisation_management import mint_generic_model
#from sciunit.models.runnable import RunnableModel


try:
    import asciiplotlib as apl
except:
    pass
class DataTC(object):
    '''
    Data Transport Container

    This Object class serves as a data type for storing rheobase search
    attributes and apriori model parameters,
    with the distinction that unlike the NEURON model this class
    can be cheaply transported across HOSTS/CPUs
    '''
    def __init__(self):
        self.lookup = {}
        self.rheobase = None
        self.previous = 0
        self.run_number = 0
        self.attrs = None
        self.steps = None
        self.name = None
        self.results = None
        self.fitness = None
        self.score = None
        self.scores = None

        self.boolean = False
        self.initiated = False
        self.delta = []
        self.evaluated = False
        self.results = {}
        self.searched = []
        self.searchedd = {}
        self.cached_attrs = {}
        self.predictions = {}
        self.observations = {}
        self.backend = None
        self.summed = None
        self.constants = None
        self.scores_ratio = None
        self.from_imputation = False
        self.preds = {}
        self.td = {}
    def get_ss(self):
        # get summed score
        if self.scores is not None:
            if len(self.scores) == 1:
                self.summed = list(self.scores.values())[0]
            else:
                self.summed = np.sum(list(self.scores.values()))
        else:
            self.summed = None
        return self.summed

    def add_constant(self):
        if self.constants is not None:
            self.attrs.update(self.constants)
        return #self.attrs
    def dtc_to_model(self):
        from neuronunit.models import VeryReducedModel
        #model = RunnableModel(str(self.backend),backend=self.backend,attrs=self.attrs)
        #model = RunnableModel(str(self.backend),backend=(self.backend, {'DTC':self}))
        model = VeryReducedModel(backend=(self.backend, {'DTC':self}))#, {'DTC':dtc}))
        # If  test taking data, and objects are present (observations etc).
        # Take the rheobase test and store it in the data transport container.
        if not hasattr(self,'scores'):
            self.scores = None
        if type(self.scores) is type(None):
            self.scores = {}
        model.attrs = self.attrs
        model.scores = self.scores
        model.rheobase = self.rheobase
        try:
            model.inj = self.params
        except:
            try:
                model.inj = self.vparams
            except:
                model.inj = None
        return model
    def dtc_to_gene(self):
        from neuronunit.optimisation.optimization_management import WSListIndividual
        print('warning translation dictionary should be used, to garuntee correct attribute order from random access dictionaries')
        if hasattr(self,'td'):
            print(self.td)
            gene = WSListIndividual(list(self.attrs.values()))

        else:
            gene = WSListIndividual(list(self.attrs.values()))
        return gene
                                    
    def judge_test(self,index=0):
        model = self.dtc_to_model()
        if not hasattr(self,'tests'):
            print('warning dtc object does not contain NU-tests yet')
            return dtc

        ts = self.tests
        #this_test = ts[index]
        if not hasattr(self,'preds'):
            self.preds = {}
        filteredt = [this_test for this_test in self.tests if type(this_test) is not type('str')]
        for this_test in filteredt:
            if this_test.passive:
                this_test.setup_protocol(model)
                pred = this_test.extract_features(model,this_test.get_result(model))
            else:
                pred = this_test.generate_prediction(model)
            self.preds[this_test.name] = pred
        return self.preds

    def check_params(self):
        self.judge_test()
        print(self.rheobase)
        print(self.vparams)
        print(self.params)
        return self.preds
    def plot_obs(self,ow):
        '''
        assuming a waveform exists (observed waved-form) plot to terminal with ascii
        This is useful for debugging new backends, in bash big/fast command line orientated optimization routines.
        '''

        t = [float(f) for f in ow.times]
        v = [float(f) for f in ow.magnitude]
        fig = apl.figure()
        fig.plot(t, v, label=str('observation waveform from inside dtc: '), width=100, height=20)
        fig.show()

    def iap(self):
        '''
        Inject and plot to terminal with ascii
        This is useful for debugging new backends, in bash big/fast command line orientated optimization routines.
        '''

        model = self.dtc_to_model()
        #new_tests['RheobaseTest']
        if type(self.tests) is type({'1':1}):
            if 'RheobaseTest' in self.tests.keys():
                uset_t = self.tests['RheobaseTest']
            else:
                uset_t = self.tests['RheobaseTestP']
        
        elif type(self.tests) is type(list):
            for t in self.tests:
                if t.name in str('RheobaseTest'):
                    uset_t = t
                    break

        pms = uset_t.params
        pms['injected_square_current']['amplitude'] = self.rheobase
        print(pms)
        model.inject_square_current(pms['injected_square_current'])
        nspike = model.get_spike_train()
        print(nspike)
        vm = model.get_membrane_potential()
        t = [float(f) for f in vm.times]
        v = [float(f) for f in vm.magnitude]
        try:
            fig = apl.figure()
            fig.plot(t, v, label=str('observation waveform from inside dtc: ')+str(nspike), width=100, height=20)
            fig.show()
        except:
            import warnings
            print('ascii plot not installed')
        return vm
