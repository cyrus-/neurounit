import time
import pdb
import array
import random
import copy

"""
Scoop can only operate on variables classes and methods at top level 0
This means something with no indentation, no nesting,
and no virtual nesting (like function decorators etc)
anything that starts at indentation level 0 is okay.

However the case may be different for functions. Functions may be imported from modules.
I am unsure if it is only the case that functions can be imported from a module, if they are not bound to
any particular class in that module.

Code from the DEAP framework, available at:
https://code.google.com/p/deap/source/browse/examples/ga/onemax_short.py
from scoop import futures
"""

import numpy as np
import matplotlib.pyplot as plt
import quantities as pq
from deap import algorithms
from deap import base
from deap.benchmarks.tools import diversity, convergence, hypervolume
from deap import creator
from deap import tools
from scoop import futures
import scoop

import get_neab

import quantities as qt
import os
import os.path
from scoop import utils

import sciunit.scores as scores


init_start=time.time()
creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0, -1.0,
                                                    -1.0, -1.0, -1.0, -1.0))
creator.create("Individual",list, fitness=creator.FitnessMin)

class Individual(object):
    '''
    When instanced the object from this class is used as one unit of chromosome or allele by DEAP.
    Extends list via polymorphism.
    '''
    def __init__(self, *args):
        list.__init__(self, *args)
        self.error=None
        self.results=None
        self.name=''
        self.attrs={}
        self.params=None
        self.score=None
        self.fitness=None
        self.s_html=None
        self.lookup={}
        self.rheobase=None
toolbox = base.Toolbox()

import model_parameters as params

vr = np.linspace(-75.0,-50.0,1000)
a = np.linspace(0.015,0.045,1000)
b = np.linspace(-3.5*10E-9,-0.5*10E-9,1000)
k = np.linspace(7.0E-4-+7.0E-5,7.0E-4+70E-5,1000)
C = np.linspace(1.00000005E-4-1.00000005E-5,1.00000005E-4+1.00000005E-5,1000)

c = np.linspace(-55,-60,1000)
d = np.linspace(0.050,0.2,1000)
v0 = np.linspace(-75.0,-45.0,1000)
vt =  np.linspace(-50.0,-30.0,1000)
vpeak= np.linspace(20.0,30.0,1000)

param=['vr','a','b','C','c','d','v0','k','vt','vpeak']
rov=[]

rov.append(vr)
rov.append(a)
rov.append(b)
rov.append(C)
rov.append(c)

rov.append(d)
rov.append(v0)
rov.append(k)
rov.append(vt)
rov.append(vpeak)

BOUND_LOW=[ np.min(i) for i in rov ]
BOUND_UP=[ np.max(i) for i in rov ]

NDIM = len(param)

import functools

def uniform(low, up, size=None):
    try:
        return [random.uniform(a, b) for a, b in zip(low, up)]
    except TypeError:
        return [random.uniform(a, b) for a, b in zip([low] * size, [up] * size)]

toolbox.register("attr_float", uniform, BOUND_LOW, BOUND_UP, NDIM)
toolbox.register("Individual", tools.initIterate, creator.Individual, toolbox.attr_float)
import deap as deap

toolbox.register("population", tools.initRepeat, list, toolbox.Individual)
toolbox.register("select", tools.selNSGA2)

import grid_search as gs
model = gs.model

def evaluate(individual,iter_):#This method must be pickle-able for scoop to work.
    '''
    Inputs: An individual gene from the population that has compound parameters, and a tuple iterator that
    is a virtual model object containing an appropriate parameter set, zipped togethor with an appropriate rheobase
    value, that was found in a previous rheobase search.

    outputs: a tuple that is a compound error function that NSGA can act on.

    Assumes rheobase for each individual virtual model object (vms) has already been found
    there should be a check for vms.rheobase, and if not then error.
    Inputs a gene and a virtual model object.
    outputs are error components.
    '''
    print(iter_)
    gen,vms,rheobase=iter_
    print(vms,rheobase)
    print(vms.rheobase)
    assert vms.rheobase==rheobase

    import quantities as pq
    params = gs.params
    model = gs.model
    if rheobase == None:
        #Assign a high error
        error = [ 100.0 for i in range(0,8) ]
    else:
        uc = {'amplitude':rheobase}
        current = params.copy()['injected_square_current']
        current.update(uc)
        current = {'injected_square_current':current}
        #Its very important to reset the model here. Such that its vm is new, and does not carry charge from the last simulation
        model.re_init(vms.attrs)#purge models stored charge. by reinitializing it
        model.load_model()
        model.update_run_params(vms.attrs)
        model.inject_square_current(current)
        import neuronunit.capabilities as cap
        import matplotlib.pyplot as plt

        n_spikes = model.get_spike_count()
        #if n_spikes == 0 and rheobase == 0.0:

        if n_spikes == 1 and rheobase != 0.0 :
            plt.plot(model.results['t'],model.results['vm'],label='candidate of GA')
            plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                       ncol=2, mode="expand", borderaxespad=0.)

            plt.title(str(vms.rheobase*pq.pA)+str(gen))
            plt.savefig(str('all_rheobase_injections')+'gen'+'_'+str(gen)+'_'+str(vms.rheobase*pq.pA)+str('.png'))

        assert n_spikes == 1 or n_spikes == 0  # Its possible that no rheobase was found
        #filter out such models from the evaluation.

        sane = False
        #init error such that there is no chance it can become none.

        inderr = getattr(individual, "error", None)
        if inderr!=None:
            if len(individual.error)!=0:
                #the average of 10 and the previous score is chosen as a nominally high distance from zero
                error = [ (abs(-10.0+i)/2.0) for i in individual.error ]
                #pdb.set_trace()
        else:
            #10 is chosen as a nominally high distance from zero
            error = [ 100.0 for i in range(0,8) ]

        sane = get_neab.suite.tests[0].sanity_check(vms.rheobase*pq.pA,model)
        if sane == True and n_spikes == 1:
            for i in [4,5,6]:
                get_neab.suite.tests[i].params['injected_square_current']['amplitude']=vms.rheobase*pq.pA
            get_neab.suite.tests[0].prediction={}
            if vms.rheobase == 0:
                vms.rheobase = 1E-10
            assert vms.rheobase != None
            score = get_neab.suite.tests[0].prediction['value']=vms.rheobase*pq.pA
            score = get_neab.suite.judge(model)#passing in model, changes model


            spikes_numbers=[]
            model.run_number+=1
            error = score.sort_key.values.tolist()[0]
            for x,y in enumerate(error):
                if y != None and x == 0 :
                    error[x] = abs(vms.rheobase - get_neab.suite.tests[0].observation['value'].item())
                elif y != None and x!=0:
                    error[x]= abs(y-0.0)+error[0]
                elif y == None:
                    inderr = getattr(individual, "error", None)
                    if inderr!=None:
                        error[x]= abs(inderr[x]-10)/2.0 + error[0]
                    else:
                        error[x] = 10.0 + error[0]

        print(error)
        individual.error = error
        import copy
        individual.rheobase = copy.copy(vms.rheobase)
    return error[0],error[1],error[2],error[3],error[4],error[5],error[6],error[7],




toolbox.register("evaluate", evaluate)
toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0)
toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0/NDIM)
toolbox.register("select", tools.selNSGA2)
toolbox.register("map", futures.map)


def plotss(vmlist,gen):
    import matplotlib.pyplot as plt
    plt.clf()
    for ind,j in enumerate(vmlist):
        if hasattr(ind,'results'):
            plt.plot(ind.results['t'],ind.results['vm'],label=str(vmlist[j].attr) )
            #plt.xlabel(str(vmlist[j].attr))
    plt.savefig('snap_shot_at_gen_'+str(gen)+'.png')
    plt.clf()


def individual_to_vm(ind):
    for i, p in enumerate(param):
        value = str(ind[i])
        if i == 0:
            attrs={'//izhikevich2007Cell':{p:value }}
        else:
            attrs['//izhikevich2007Cell'][p] = value
    vm = gs.VirtualModel()
    vm.attrs = attrs

    inderr = getattr(ind, "error", None)
    if inderr!=None:
        vm.error = ind.error
        #print('vm.error: ',vm.error)
    indrheobase = getattr(ind, "rheobase", None)
    if indrheobase!=None:
        vm.rheobase = ind.rheobase
        #print('vm.rheobase: ',vm.rheobase)

    return vm

def replace_rh(pop,MU,rh_value,vmpop):
    rheobase_checking=gs.evaluate
    from itertools import repeat
    #invalid_ind = [ ind for i,ind in enumerate(pop) if not vmpop[i].rheobase == None ]
    print(len(pop), ' length population')
    pop = [ ind for i,ind in enumerate(pop) if not vmpop[i].rheobase == None ]
    vmpop = [ ind for i,ind in enumerate(vmpop) if not vmpop[i].rheobase == None ]

    for i,ind in enumerate(pop):
        print(i,ind, 'this prob does not execute too' )
        print(vmpop[i].rheobase, ' vmpop[i].rheobase')

        if vmpop[i].rheobase == None:
            print('this never executes')
            print(type(vmpop[i]))
            print(type(pop[i]))

            #del pop[i]
            #del vmpop[i]
    print(len(vmpop))
    print(len(pop))
    #assert len(pop)!=0
    assert len(vmpop)!=0
    assert len(pop)!=0

    assert len(vmpop) == len(pop)
    #print(before,after, ' before, after')

    diff = abs(len(pop) - MU)
    print(diff)
    while diff > 0:
        diff_pop = [ toolbox.Individual() for i in range(0,diff) ]
                #def assign_param(param):
        for diff_pop_ind in diff_pop:
            for i, p in enumerate(param):
                value=str(diff_pop_ind[i])
                model.name=str(model.name)+' '+str(p)+str(value)
                if i==0:
                    attrs={'//izhikevich2007Cell':{p:value }}
                else:
                    attrs['//izhikevich2007Cell'][p]=value
            diff_pop_ind.attrs=attrs

        diff_pop = list(futures.map(rheobase_checking,diff_pop,repeat(rh_value)))
        for i,j in enumerate(diff_pop):
            if j.rheobase != None:
                pop.append(diff_pop[i])

        vmpop = list(futures.map(individual_to_vm,pop))
        #vmpop.extend(list(futures.map(individual_to_vm,diff_pop)))



        assert len(vmpop) == len(pop)
        assert len(vmpop) == len(pop)
        diff = abs(len(pop) - MU)

    #invalid_ind = [ ind for ind in pop ]
    return pop, vmpop

def main():


    NGEN=6
    MU=8#Mu must be some multiple of 8, such that it can be split into even numbers over 8 CPUs

    CXPB = 0.9
    import numpy as numpy
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    hof = tools.ParetoFront()

    stats.register("avg", numpy.mean, axis=0)
    stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    pop = toolbox.population(n=MU)
    #create the first population of individuals
    guess_attrs=[]

    #find rheobase on a model constructed out of the mean parameter values.
    for x,y in enumerate(param):
        guess_attrs.append(np.mean( [ i[x] for i in pop ]))

    from itertools import repeat
    mean_vm = gs.VirtualModel()
    #def assign_param(param):
    for i, p in enumerate(param):
        value=str(guess_attrs[i])
        model.name=str(model.name)+' '+str(p)+str(value)
        if i==0:
            attrs={'//izhikevich2007Cell':{p:value }}
        else:
            attrs['//izhikevich2007Cell'][p]=value
    mean_vm.attrs=attrs
    import copy

    steps = np.linspace(50,150,7.0)
    steps_current = [ i*pq.pA for i in steps ]
    rh_param=(False,steps_current)
    searcher=gs.searcher
    check_current=gs.check_current
    pre_rh_value=searcher(check_current,rh_param,mean_vm)
    rh_value=pre_rh_value.rheobase
    global vmpop
    if rh_value == None:
        rh_value = 0.0
    vmpop = list(map(individual_to_vm,pop))

    #Now attempt to get the rheobase values by first trying the mean rheobase value.
    #This is not an exhaustive search that results in found all rheobase values
    #It is just a trying out an educated guess on each individual in the whole population as a first pass.
    #invalid_ind = [ ind for ind in pop if not ind.fitness.valid ]

    rheobase_checking=gs.evaluate


    vmpop = list(futures.map(rheobase_checking,vmpop,repeat(rh_value)))
    rhstorage = [i.rheobase for i in vmpop]
    generations = [0 for i in vmpop]

    before=len(vmpop)
    pop,vmpop = replace_rh(pop,MU,rh_value,vmpop)
    after=len(vmpop)
    assert before==after

    iter_ = zip(generations,vmpop,rhstorage)

    assert len(pop)==len(vmpop)

    #Now get the fitness of genes:
    #Note the evaluate function called is different
    fitnesses = list(toolbox.map(toolbox.evaluate, pop, iter_))

    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit
        #pdb.set_trace()
    invalid_ind = [ ind for ind in pop if not ind.fitness.valid ]
    #purge individuals for which rheobase was not found

    #insert function call here.

    #invalid_ind = [ ind for ind in pop if not ind.rheobase == None ]
    print(len(invalid_ind))
    #assert len(fitnesses)==len(invalid_ind)




    # This is just to assign the crowding distance to the individuals
    # no actual selection is done
    pop = tools.selNSGA2(pop, MU)

    record = stats.compile(pop)
    logbook.record(gen=0, evals=len(invalid_ind), **record)

    # Begin the generational process
    for gen in range(1, NGEN):
        # Vary the population


        before=len(vmpop)
        pop, vmpop = replace_rh(pop,MU,rh_value,vmpop)
        after=len(vmpop)
        assert before == after
        #print('why is mu shrinking')
        print(len(pop), MU)
        invalid_ind = [ ind for ind in pop if not ind.fitness.valid ]
        #assert len(invalid_ind) == len(pop)
        #for p in pop:
        #    print(type(p),p)
        offspring = tools.selNSGA2(invalid_ind, len(invalid_ind))
        #offspring = tools.selTournamentDCD(invalid_ind, len(invalid_ind))
        offspring = [toolbox.clone(ind) for ind in offspring]



        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() <= CXPB:
                toolbox.mate(ind1, ind2)

            toolbox.mutate(ind1)
            toolbox.mutate(ind2)
            del ind1.fitness.values, ind2.fitness.values

        #pop = tools.selNSGA2(pop,MU)


        vmpop=list(futures.map(individual_to_vm,offspring))
        vmpop=list(futures.map(rheobase_checking,vmpop,repeat(rh_value)))
        rhstorage = [i.rheobase for i in vmpop]
        generations = [ gen for i,j in enumerate(vmpop) ]
        iter_ = zip(generations,vmpop,rhstorage)
        before=len(vmpop)
        pop,vmpop = replace_rh(offspring,MU,rh_value,vmpop)
        after=len(vmpop)
        invalid_ind = [ ind for ind in pop if not ind.fitness.valid ]
        print(before,after, ' before, after')
        assert before==after
        #invalid_ind , pop = replace_rh(invalid_ind, pop, MU ,rh_value, vmpop)
        fitnesses = list(toolbox.map(toolbox.evaluate, invalid_ind , iter_))

        assert len(fitnesses)==len(invalid_ind)


        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop = toolbox.select(invalid_ind + offspring, MU)

        vmpop=list(futures.map(individual_to_vm,pop))
        print(len(vmpop),len(pop),' length of population')

    record = stats.compile(pop)
    logbook.record(gen=gen, evals=len(invalid_ind), **record)
    pop.sort(key=lambda x: x.fitness.values)
    f=open('best_candidate.txt','w')
    f.write(str(vmpop[-1].attrs))
    f.write(str(vmpop[-1].rheobase))

    f.write(logbook.stream)
    f.close()
    score_matrixt=[]
    score_matrixt.append((vmpop[0].error,vmpop[0].attrs,vmpop[0].rheobase))
    score_matrixt.append((vmpop[1].error,vmpop[1].attrs,vmpop[1].rheobase))

    score_matrixt.append((vmpop[-1].error,vmpop[-1].attrs,vmpop[-1].rheobase))
    import pickle
    import pickle
    with open('score_matrixt.pickle', 'wb') as handle:
        pickle.dump(score_matrixt, handle)

    with open('vmpop.pickle', 'wb') as handle:
        pickle.dump(vmpop, handle)



    return vmpop, pop, stats, invalid_ind


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import pyneuroml as pynml
    import os
    import time
    start_time=time.time()
    whole_initialisation=start_time-init_start
    model=gs.model
    vmpop, pop, stats, invalid_ind = main()

    steps = np.linspace(50,150,7.0)
    steps_current = [ i*pq.pA for i in steps ]
    rh_param = (False,steps_current)
    searcher = gs.searcher
    check_current = gs.check_current
    print(vmpop)

    score_matrixt=[]
    vmpop=list(map(individual_to_vm,pop))

    pdb.set_trace()
    #assert vmpop.error !=
