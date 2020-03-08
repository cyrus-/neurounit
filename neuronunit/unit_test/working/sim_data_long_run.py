
# coding: utf-8

# # Set up the environment

import matplotlib.pyplot as plt
import matplotlib
import hide_imports
from neuronunit.optimisation.optimization_management import inject_and_plot_model, inject_and_plot_passive_model
import copy
import pickle
from neuronunit.optimisation.optimization_management import check_match_front


# # Design simulated data tests

def jrt(use_test,backend):
    use_test = hide_imports.TSD(use_test)
    use_test.use_rheobase_score = True
    edges = hide_imports.model_parameters.MODEL_PARAMS[backend]
    OM = hide_imports.OptMan(use_test,
        backend=backend,
        boundary_dict=edges,
        protocol={'allen': False, 'elephant': True})

    return OM


def sim_data_tests(backend,MU,NGEN):
    test_frame = pickle.load(open('processed_multicellular_constraints.p','rb'))
    stds = {}
    for k,v in hide_imports.TSD(test_frame['Neocortex pyramidal cell layer 5-6']).items():
        temp = hide_imports.TSD(test_frame['Neocortex pyramidal cell layer 5-6'])[k]
        stds[k] = temp.observation['std']
    OMObjects = []
    cloned_tests = copy.copy(test_frame['Neocortex pyramidal cell layer 5-6'])

    OM = jrt(cloned_tests,backend)
    rt_outs = []

    x= {k:v for k,v in OM.tests.items() if 'mean' in v.observation.keys() or 'value' in v.observation.keys()}
    cloned_tests = copy.copy(OM.tests)
    OM.tests = hide_imports.TSD(cloned_tests)
    rt_out = OM.simulate_data(OM.tests,OM.backend,OM.boundary_dict)
    penultimate_tests = hide_imports.TSD(test_frame['Neocortex pyramidal cell layer 5-6'])
    for k,v in penultimate_tests.items():
        temp = penultimate_tests[k]

        v = rt_out[1][k].observation
        v['std'] = stds[k]
    simulated_data_tests = hide_imports.TSD(penultimate_tests)


    # # Show what the randomly generated target waveform the optimizer needs to find actually looks like


    target = rt_out[0]
    target.rheobase


    # # first lets just optimize over all objective functions all the time.
    # # Commence optimization of models on simulated data sets


    ga_out = simulated_data_tests.optimize(
                                        OM.boundary_dict,backend=OM.backend,
                                        protocol={'allen': False, 'elephant': True},
                                        MU=MU,NGEN=NGEN)

    ga_out['DO'] = None
    front_only = copy.copy(ga_out['pf'])
    for d in front_only:
        d.dtc.tests.DO = None
        d.dtc.tests = d.dtc.tests.to_dict()
    opt = ga_out['pf'][0].dtc
    #target

    target.DO = None
    #target.tests = d.dtc.tests.to_dict()
    front = [ind.dtc for ind in ga_out['pf']]

    check_match_front(target,front[0:10],figname ='front'+str('MU_')+str(MU)+('_NGEN_')+str(NGEN)+str(backend)+'_.png')
    inject_and_plot_model(target,figname ='just_target_of_opt_'+str('MU_')+str(MU)+('_NGEN_')+str(NGEN)+str(backend)+'_.png')
    inject_and_plot_model(opt,figname ='just_opt_active_'+str('MU_')+str(MU)+('_NGEN_')+str(NGEN)+str(backend)+'_.png')
    inject_and_plot_passive_model(opt,figname ='just_opt_'+str('MU_')+str(MU)+('_NGEN_')+str(NGEN)+str(backend)+'_.png')#,figname=None)

    with open('sim data.p','wb') as f:
        pickle.dump([target,opt.obs_preds],f)


    sim_data = pickle.load(open('sim data.p','rb'))

    return ga_out,target,front

MU = NGEN = 35
backend = str("HH")

ga_out,target,front = sim_data_tests(backend,MU,NGEN)
'''
backend = str("HH")

ga_out,target,front = sim_data_tests(backend,MU,NGEN)
'''
