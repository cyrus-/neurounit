
import os,sys
import numpy as np
import matplotlib.pyplot as plt
import quantities as pq
import sciunit

#Over ride any neuron units in the PYTHON_PATH with this one.
#only appropriate for development.
thisnu = str(os.getcwd())+'/../..'
sys.path.insert(0,thisnu)
print(sys.path)

import neuronunit
from neuronunit import aibs
from neuronunit.models.reduced import ReducedModel
import pdb
import pickle

IZHIKEVICH_PATH = os.getcwd()+str('/NeuroML2') # Replace this the path to your
LEMS_MODEL_PATH = IZHIKEVICH_PATH+str('/LEMS_2007One.xml')


import time

from pyneuroml import pynml

import quantities as pq
from neuronunit import tests as nu_tests, neuroelectro
neuron = {'nlex_id': 'nifext_50'} # Layer V pyramidal cell
tests = []

dataset_id = 354190013  # Internal ID that AIBS uses for a particular Scnn1a-Tg2-Cre
                        # Primary visual area, layer 5 neuron.
observation = aibs.get_observation(dataset_id,'rheobase')


if os.path.exists(str(os.getcwd())+"/neuroelectro.pickle"):
    print('attempting to recover from pickled file')
    with open('neuroelectro.pickle', 'rb') as handle:
        tests = pickle.load(handle)

else:
    print('checked path:')
    print(str(os.getcwd())+"/neuroelectro.pickle")
    print('no pickled file found. Commencing time intensive Download')

    #(nu_tests.TimeConstantTest,None),                           (nu_tests.InjectedCurrentAPAmplitudeTest,None),
    tests += [nu_tests.RheobaseTest(observation=observation)]
    test_class_params = [(nu_tests.InputResistanceTest,None),
                         (nu_tests.RestingPotentialTest,None),
                         (nu_tests.InjectedCurrentAPWidthTest,None),
                         (nu_tests.InjectedCurrentAPThresholdTest,None)]



    for cls,params in test_class_params:
        #use of the variable 'neuron' in this conext conflicts with the module name 'neuron'
        #at the moment it doesn't seem to matter as neuron is encapsulated in a class, but this could cause problems in the future.


        observation = cls.neuroelectro_summary_observation(neuron)
        tests += [cls(observation,params=params)]

    with open('neuroelectro.pickle', 'wb') as handle:
        pickle.dump(tests, handle)

def update_amplitude(test,tests,score):
    rheobase = score.prediction['value']#first find a value for rheobase
    #then proceed with other optimizing other parameters.


    print(len(tests))
    #pdb.set_trace()
    for i in [2,3,4]:
        # Set current injection to just suprathreshold
        tests[i].params['injected_square_current']['amplitude'] = rheobase*1.01


#Do the rheobase test. This is a serial bottle neck that must occur before any parallel optomization.
#Its because the optimization routine must have apriori knowledge of what suprathreshold current injection values are for each model.

hooks = {tests[0]:{'f':update_amplitude}} #This is a trick to dynamically insert the method
#update amplitude at the location in sciunit thats its passed to, without any loss of generality.
suite = sciunit.TestSuite("vm_suite",tests,hooks=hooks)

from neuronunit.models import backends
from neuronunit.models.reduced import ReducedModel
model = ReducedModel(LEMS_MODEL_PATH,name='vanilla',backend='NEURON')
model=model.load_model()
model.local_run()


from types import MethodType




import pdb
import numpy as np

import random
import array
import random
import scoop as scoop
import numpy as np, numpy
import scoop
from math import sqrt
from scoop import futures
from deap import algorithms
from deap import base
from deap import benchmarks
#from deap.benchmarks.tools import diversity, convergence, hypervolume
from deap import creator
from deap import tools

#def optimize(self,model,rov,param):
best_params = None
best_score = None
#from neuronunit.deapcontainer.deap_container2 import DeapContainer
#dc=DeapContainer()
pop_size=12
ngen=4


from types import MethodType
#def optimize(self,model,rov,param):
best_params = None
best_score = None
#from neuronunit.deapcontainer.deap_container2 import DeapContainer
#dc=DeapContainer()
pop_size=12
ngen=4


toolbox = base.Toolbox()
creator.create("FitnessMax", base.Fitness, weights=(-1.0,-1.0,-1.0,-1.0,-1.0,-1.0,))#Final comma here, important, not a typo, must be a tuple type.
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMax)


class Individual(list):
    '''
    When instanced the object from this class is used as one unit of chromosome or allele by DEAP.
    Extends list via polymorphism.
    '''
    def __init__(self, *args):
        list.__init__(self, *args)
        self.error=None

        self.sciunitscore=[]
        self.model=None
        self.error=None
        self.results=None
        self.name=''
        self.attrs={}
        self.params=None
        self.score=None


def uniform(low, up, size=None):
    '''
    This is the PRNG distribution that defines the initial
    allele population. Inputs are the maximum and minimal numbers that the PRNG can generate.
    '''
    try:
        return [random.uniform(a, b) for a, b in zip(low, up)]
    except TypeError:
        return [random.uniform(a, b) for a, b in zip([low] * size, [up] * size)]



name=None
attrs=None
name_value=None
error=None
score=None
BOUND_LOW=[ np.min(i) for i in rov ]
BOUND_UP=[ np.max(i) for i in rov ]
NDIM = len(rov)


toolbox.register("map",map)
toolbox.register("attr_float", uniform, BOUND_LOW, BOUND_UP, NDIM)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.attr_float)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def evaluate(individual):#This method must be pickle-able for scoop to work.
    #print('hello from before error')
    error=individual.error
    return (error[0],error[1],error[2],error[3],error[4],)
import dill

toolbox.register("evaluate",evaluate)

'{} {}'.format('why it cant pickle',dill.pickles(evaluate))
'{} {}'.format('why it cant pickle',dill.detect.badtypes(evaluate))
#pdb.set

def paramap(the_func,pop):


    import mpi4py
    from mpi4py import MPI
    COMM = MPI.COMM_WORLD
    SIZE = COMM.Get_size()
    RANK = COMM.Get_rank()
    import copy
    pop1=copy.copy(pop)
    #ROund robin distribution
    psteps = ( pop1[i] for i in range(RANK, len(pop1), SIZE) )
    pop=[]
    print('code hangs here why1 ?')

    print('hello from RANK \n', RANK)
    print('hello from RANK\n', RANK)
    print('hello from RANK\n', RANK)

    print('hello from RANK', RANK)
    #Do the function to list element mapping
    pop=list(map(the_func,psteps))
    #gather all the resulting lists onto rank0


    pop2 = COMM.gather(pop, root=0)
    print('code hangs here why2?')
    #COMM.barrier()
    if RANK == 0:
        print('got to past rank0 block')
        pop=[]
        #merge all of the lists into one list on rank0
        for p in pop2:
            pop.extend(p)
        print('hangs here 2')

    else:
        pop=None
        print('hangs here 3')

    if RANK==0:
        #broadcast the results back to all hosts.
        print('stuck 3')
        pop = COMM.bcast(pop, root=0)
        print('hangs here 4')
        #pdb.set_trace()

    return pop


toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0)
toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0/NDIM)
toolbox.register("select", tools.selNSGA2)

random.seed(seed_in)

CXPB = 0.9#cross over probability


stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("avg", numpy.mean, axis=0)
stats.register("std", numpy.std, axis=0)
stats.register("min", numpy.min, axis=0)
stats.register("max", numpy.max, axis=0)

logbook = tools.Logbook()
logbook.header = "gen", "evals", "std", "min", "avg", "max"

pop = toolbox.population(n=self.pop_size)

#        #for i in range(RANK, len(pop), SIZE):#
#    psteps1.append(pop[i])
#assert len(psteps)==len(psteps1)
#pop=[]
def func2map(ind):

    #print(RANK)
    ind.sciunitscore={}
    model=model.load_model()
    for i, p in enumerate(param):
        name_value=str(ind[i])
        #reformate values.
        self.model.name=name_value
        if i==0:
            attrs={'//izhikevich2007Cell':{p:name_value }}
        else:
            attrs['//izhikevich2007Cell'][p]=name_value

    self.model.update_run_params(attrs)
    import copy

    ind.results=copy.copy(self.model.results)
    #print(type(ind))
    #ind.attrs=attrs
    #ind.name=name_value
    #ind.params=p
    score = test_or_suite.judge(model)
    ind.error = copy.copy(score.sort_keys.values[0])
    return ind

#pop=paramap(func2map,pop)
#pop=v.map(func2map,pop)
pop=list(map(func2map,pop))
#pop = toolbox.map(func2map,pop)

#pop=map_function(func2map,pop)
#pdb.set_trace()
invalid_ind = [ind for ind in pop if not ind.fitness.valid]
#for ind in invalid_ind:
#    print(hasattr(ind,'error'))
print('this is where I should check what attributes ind in pop has')

fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
for ind, fit in zip(invalid_ind, fitnesses):
    print(ind,fit)
    ind.fitness.values = fit
    print(ind.fitness.values)


# This is just to assign the crowding distance to the individuals
# no actual selection is done
pop = toolbox.select(pop, len(pop))
#pop = toolbox.select(pop, len(pop))

record = stats.compile(pop)
logbook.record(gen=0, evals=len(invalid_ind), **record)
print(logbook.stream)

stats_fit = tools.Statistics(key=lambda ind: ind.fitness.values)
stats_size = tools.Statistics(key=len)
mstats = tools.MultiStatistics(fitness=stats_fit, size=stats_size)
record = mstats.compile(pop)

# Begin the generational process
def sciunitoptime():
    for gen in range(1,self.ngen):
        # Vary the population
        offspring = tools.selTournamentDCD(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]

        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() <= CXPB:
                toolbox.mate(ind1, ind2)
            print('ind1 is updating: ')
            print(ind1,ind2)
            toolbox.mutate(ind1)
            toolbox.mutate(ind2)
            del ind1.fitness.values, ind2.fitness.values
            print('stuck y')
            #pdb.set_trace()


        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        print('stuck x')
        #pdb.set_trace()
        #fitnesses = list(map(callsciunitjudge,invalid_ind))
        #fitnesses = paramap(callsciunitjudge,invalid_ind)
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)

        #fitnesses=v.map(callsciunitjudge,invalid_ind)

        #fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        print('gen is updating: ', gen)
        print(gen)
        print(record)

    return pop


#toolbox = base.Toolbox()
#from scoop import futures
if __name__ == '__main__':

#toolbox.register("map", futures.map)
    my_test = tests[0]
    my_test.verbose = True
    my_test.optimize = sciunitopt(optimize, my_test) # Bind to the score.


    param=['vr','a','b']
    rov=[]
    rov0 = np.linspace(-65,-55,1000)
    rov1 = np.linspace(0.015,0.045,7)
    rov2 = np.linspace(-0.0010,-0.0035,7)
    rov.append(rov0)
    rov.append(rov1)
    rov.append(rov2)
    before_ga=time.time()
    pop = my_test.optimize(model,rov,param)
    after_ga=time.time()
    print('the time was:')
    delta=after_ga-before_ga
    print(delta)


    #This needs to act on error.
    #pdb.set_trace()
    #if RANK==0:
        #print("%.2f mV" % np.mean([p[0] for p in pop]))


    import matplotlib as matplotlib
    matplotlib.use('agg')
    import matplotlib.pyplot as plt
    plt.hold(True)
    for i in range(0,9):
        plt.plot(pop[i].time_trace,pop[i].voltage_trace)
    plt.savefig('best 10')