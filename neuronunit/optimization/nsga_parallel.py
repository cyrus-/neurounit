#import matplotlib # Its not that this file is responsible for doing plotting, but it calls many modules that are, such that it needs to pre-empt
# setting of an appropriate backend.
#matplotlib.use('agg')

import numpy as np
import dask.bag as db
import pandas as pd
# Import get_neab has to happen exactly here. It has to be called only on
from neuronunit import tests
from neuronunit.optimization import get_neab

def dtc_to_rheo(dtc):
    from neuronunit.models.reduced import ReducedModel
    from neuronunit.optimization import get_neab
    dtc.model_path = get_neab.LEMS_MODEL_PATH
    dtc.LEMS_MODEL_PATH = get_neab.LEMS_MODEL_PATH
    model = ReducedModel(dtc.LEMS_MODEL_PATH,name=str('vanilla'),backend='NEURON')
    model.set_attrs(dtc.attrs)
    dtc.scores = {}
    dtc.score = {}
    score = get_neab.tests[0].judge(model,stop_on_error = False, deep_error = True)
    dtc.rheobase = score.prediction
    assert dtc.rheobase is not None
    dtc.scores[str(get_neab.tests[0])] = 1 - score.sort_key #pd.DataFrame([ ])
    return dtc

def dtc_to_plotting(dtc):
    '''
    Inputs a data transport container, containing either no recording vectors,
    or existing recording vectors that are intended to be over written with fresh ones.
    outputs a data transport container with recording vectors added.
    '''
    import copy
    dtc = copy.copy(dtc)
    dtc.t = None
    from neuronunit.models.reduced import ReducedModel
    from neuronunit.optimization import get_neab
    model = ReducedModel(get_neab.LEMS_MODEL_PATH,name=str('vanilla'),backend='NEURON')
    model.set_attrs(dtc.attrs)
    model.rheobase = dtc.rheobase['value']
    score = get_neab.tests[-1].judge(model,stop_on_error = False, deep_error = True)
    dtc.vm = list(model.results['vm'])
    dtc.t = list(model.results['time'])
    return dtc

def nunit_evaluation(dtc):
    '''
    Inputs single data transport container modules.
    Outputs
    Neuron Unit evaluation
    '''
    assert dtc.rheobase is not None

    from neuronunit.models.reduced import ReducedModel
    from neuronunit.optimization import get_neab
    tests = get_neab.tests
    model = None
    model = ReducedModel(get_neab.LEMS_MODEL_PATH,name=str('vanilla'),backend='NEURON')#('pyNN',{'DTC':dtc}))
    model.set_attrs(dtc.attrs)
    tests[0].prediction = dtc.rheobase
    model.rheobase = dtc.rheobase['value']
    print(model.rheobase)


    from dask import dataframe as dd
    #sd = dd.from_pandas(df, npartitions=3)
    if dtc.score is None:
        dtc.score = {}

    for k,t in enumerate(tests[1:-1]):
        t.params = dtc.vtest[k]
        print(t.params)
        score = None
        score = t.judge(model,stop_on_error = False, deep_error = False)
        try:
            bool(model.get_spike_count() == 1 or model.get_spike_count() == 0)
            dtc.scores.get(str(t), score.sort_key)
            dtc.score.get(str(t), score.sort_key-1)
            '''
            dtc.get("scores",)
            scores = {}
            dtc.scores[str(t)] = 1 - score.sort_key
            if not hasattr(dtc,'score') :
                dtc.score = {}
                dtc.score[str(t)] = score.sort_key
            else:
                dtc.score[str(t)] = score.sort_key
            '''
        except:
            pass

    return dtc


def evaluate(dtc):
    import copy
    dtc = copy.copy(dtc)

    from neuronunit.optimization import get_neab
    import numpy as np
    fitness = [ 1.0 for i in range(0,7) ]

    for k,t in enumerate(dtc.scores.keys()):
        fitness[k] = dtc.scores[str(t)]#.sort_key
    #fitness[7] = np.sum(list(fitness[0:6]))
    print(fitness)
    return fitness[0],fitness[1],\
           fitness[2],fitness[3],\
           fitness[4],fitness[5],\
           fitness[6],#fitness[7]



def get_trans_list(param_dict):
    trans_list = []
    for i,k in enumerate(list(param_dict.keys())):
        trans_list.append(k)
    return trans_list

def pre_format(dtc):
    '''
    pre format the current injection dictionary based on pre computed
    rheobase values of current injection.
    This is much like the hooked method from the old get neab file.
    '''
    import copy
    dtc = copy.copy(dtc)
    import quantities as pq
    import copy
    dtc.vtest = None
    dtc.vtest = {}
    from neuronunit.optimization import get_neab
    tests = get_neab.tests
    for k,v in enumerate(tests):
        dtc.vtest[k] = {}
        dtc.vtest[k]['injected_square_current'] = {}
    for k,v in enumerate(tests):
        if k == 1 or k == 2 or k == 3:
            # Negative square pulse current.
            dtc.vtest[k]['injected_square_current']['duration'] = 100 * pq.ms
            dtc.vtest[k]['injected_square_current']['amplitude'] = -10 *pq.pA
            dtc.vtest[k]['injected_square_current']['delay'] = 30 * pq.ms

        if k == 0 or k == 4 or k == 5 or k == 6 or k == 7:
            # Threshold current.
            dtc.vtest[k]['injected_square_current']['duration'] = 1000 * pq.ms
            dtc.vtest[k]['injected_square_current']['amplitude'] = dtc.rheobase['value']
            dtc.vtest[k]['injected_square_current']['delay'] = 250 * pq.ms # + 150
    return dtc



def update_dtc_pop(pop, td, backend = None):

    '''
    inputs a population of genes/alleles, the population size MU, and an optional argument of a rheobase value guess
    outputs a population of genes/alleles, a population of individual object shells, ie a pickleable container for gene attributes.
    Rationale, not every gene value will result in a model for which rheobase is found, in which case that gene is discarded, however to
    compensate for losses in gene population size, more gene samples must be tested for a successful return from a rheobase search.
    If the tests return are successful these new sampled individuals are appended to the population, and then their attributes are mapped onto
    corresponding virtual model objects.
    '''

    import copy
    import numpy as np
    from deap import base
    toolbox = base.Toolbox()
    pop = [toolbox.clone(i) for i in pop ]
    def transform(ind):
        import dask.bag as db
        from neuronunit.optimization.data_transport_container import DataTC
        dtc = DataTC()
        #dtc.backend = None

        ##
        # set the backend
        ##

        import neuronunit
        LEMS_MODEL_PATH = str(neuronunit.__path__[0])+str('/models/NeuroML2/LEMS_2007One.xml')
        dtc.backend = 'NEURON'
        if backend is not None:
            dtc.backend = backend
        #print(dtc.backend)
        dtc.attrs = {}
        for i,j in enumerate(ind):
            dtc.attrs[str(td[i])] = j
        dtc.evaluated = False
        return dtc
    if len(pop) > 1:
        b = db.from_sequence(pop, npartitions=8)
        dtcpop = list(db.map(transform,b).compute())

    else:
        # In this case pop is not really a population but an individual
        # but parsimony of naming variables
        # suggests not to change the variable name to reflect this.
        dtcpop = list(transform(pop))
    return dtcpop


def update_deap_pop(pop,td):
    '''
    Inputs a population of genes (pop).
    Returned neuronunit scored DTCs (dtcpop).
    This method converts a population of genes to a population of Data Transport Containers,
    Which act as communicatable data types for storing model attributes.
    Rheobase values are found on the DTCs
    DTCs for which a rheobase value of x (pA)<=0 are filtered out
    DTCs are then scored by neuronunit, using neuronunit models that act in place.
    '''
    import dask.bag as db
    from neuronunit.optimization import model_parameters as modelp
    # given the wrong attributes, and they don't have rheobase values.
    dtcpop = list(update_dtc_pop(pop, td))
    dtcpop = list(map(dtc_to_rheo,dtcpop))
    dtcpop = list(filter(lambda dtc: dtc.rheobase['value'] > 0.0 , dtcpop))
    while len(dtcpop) < len(pop):
        dtcpop.append(dtcpop[0])
    dtcpop = list(map(pre_format,dtcpop))
    b = db.from_sequence(dtcpop, npartitions=8)
    dtcpop = list(db.map(nunit_evaluation,b).compute())


    dtcpop = list(filter(lambda dtc: not isinstance(dtc.scores['RheobaseTestP'],type(None)), dtcpop))
    dtcpop = list(filter(lambda dtc: not type(None) in (list(dtc.scores.values())), dtcpop))


    #dtcpop = list(filter(lambda dtc: type(dtc.scores['RheobaseTestP']) is not type(None), dtcpop))
    #dtcpop = list(filter(lambda dtc: not type(None) in (list(dtc.scores.values())), dtcpop))
    ##
    # get rid of transport containers for genes that are responsible for returning None scores
    ##
    dtc_temp = []
    for dtc in dtcpop:
        temp = list(dtc.scores.values())
        if None not in temp:
            dtc_temp.append(dtc)
    dtcpop = dtc_temp
    ##
    while len(dtcpop) < len(pop):
        dtcpop.append(dtcpop[0])

    for i,d in enumerate(dtcpop):
        pop[i].rheobase = d.rheobase
    return_package = zip(dtcpop, pop)
    return return_package


def create_subset(nparams=10, provided_keys=None):
    from neuronunit.optimization import model_parameters as modelp
    import numpy as np
    mp = modelp.model_params

    key_list = list(mp.keys())

    if type(provided_keys) is type(None):
        key_list = list(mp.keys())
        reduced_key_list = key_list[0:nparams]
    else:
        reduced_key_list = provided_keys

    subset = { k:mp[k] for k in reduced_key_list }
    return subset
