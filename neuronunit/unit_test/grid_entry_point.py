USE_CACHED_GS = False
npoints = 3
nparams = 10
from neuronunit.optimization import get_neab
import os
electro_path = str(os.getcwd())+'/pipe_tests.p'
import pickle
print(electro_path)
#try:
assert os.path.isfile(electro_path) == True
with open(electro_path,'rb') as f:
    electro_tests = pickle.load(f)

electro_tests = get_neab.replace_zero_std(electro_tests)
electro_tests = get_neab.substitute_parallel_for_serial(electro_tests)
#electro_tests = []
purkinje = { 'nlex_id':'sao471801888'}#'NLXWIKI:sao471801888'} # purkinje
fi_basket = {'nlex_id':'100201'}
pvis_cortex = {'nlex_id':'nifext_50'} # Layer V pyramidal cell
olf_mitral = { 'nlex_id':'nifext_120'}
ca1_pyr = { 'nlex_id':'830368389'}

pipe = [ fi_basket, pvis_cortex, olf_mitral, ca1_pyr, purkinje ]

try:
    pass

except:
    pass
    '''
    for p in pipe:
       p_tests, p_observations = get_neab.get_neuron_criteria(p)
       electro_tests.append((p_tests, p_observations))

    electro_tests = get_neab.replace_zero_std(electro_tests)
    electro_tests = get_neab.substitute_parallel_for_serial(electro_tests)
    with open('pipe_tests.p','wb') as f:
       pickle.dump(electro_tests,f)
    '''

if USE_CACHED_GS:
    import pickle
    # shelve cache
    first_third = pickle.load(open('/home/jovyan/neuronunit/neuronunit/unit_test/grid_dump_first_3rd.p','rb'))
    second_third = pickle.load(open('/home/jovyan/neuronunit/neuronunit/unit_test/grid_dump_second_3rd.p','rb'))
    final_third = pickle.load(open('/home/jovyan/neuronunit/neuronunit/unit_test/grid_dump_final_3rd.p','rb'))

    second_third.extend(first_third)
    second_third.extend(final_third)
    dtcpopg = second_third

else:
    from neuronunit.optimization import exhaustive_search
    from neuronunit.optimization import get_neab
    from neuronunit.optimization import optimization_management

    import dask.bag as db
    grid_points = exhaustive_search.create_grid(npoints = npoints,nparams = nparams)
    pop = [list(g.values()) for g in grid_points ]
    tds = [list(g.keys()) for g in grid_points ]
    td = tds[0]
    N = 3
    cnt = 0
    from neuronunit.optimization import optimization_management
    for test, observation in electro_tests:
        pop = optimization_management.update_deap_pop(pop, test, td)
        import pickle
        with open('grid_cell'+str(pipe[cnt])+'.p','wb') as f:
           pickle.dump(pop,f)
        cnt+=1
