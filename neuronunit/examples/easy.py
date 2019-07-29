
# coding: utf-8

# In[1]:


from hide_imports import *


# In[2]:


df = pd.DataFrame(rts)


# In[ ]:


ga_outad = {}
ga_outiz = {}

for key,v in rts.items():
    local_tests = [value for value in v.values() ]
    backend = str('BAE1')
    file_name = str(key)+backend+str('.p')

    try:

        assert 1==2
        
        ga_outad[key] = pickle.load(open(filename,'rb'))
    except:
        ga_outad[key], DO = om.run_ga(model_params.MODEL_PARAMS['BAE1'],6, local_tests, free_params = model_params.MODEL_PARAMS['BAE1'],
                                    NSGA = True, MU = 10, model_type = str('ADEXP'))
        pickle.dump(ga_outad[key],open(filename,'wb'))

    backend = str('RAW')
    file_name = str(key)+backend+str('.p')
        
    try:
        assert 1==2
        ga_outiz[key] = pickle.load(open(filename,'rb'))    
        
    except:
        ga_outiz[key], DO = om.run_ga(model_params.MODEL_PARAMS['RAW'],10, local_tests, free_params = model_params.MODEL_PARAMS['RAW'],
                                    NSGA = True, MU = 10, model_type = str('RAW'))#,seed_pop=seeds[key])

        pickle.dump(ga_outiz,open(filename,'wb'))
        dtcpop = [ ind.dtc for ind in ga_outiz['pf'] ]
        


# In[ ]:



for key,v in rts.items():
    local_tests = [value for value in v.values() ]

    mp = model_params.MODEL_PARAMS['GLIF']

    mp = { k:v for k,v in mp.items() if type(v) is not dict }
    mp = { k:v for k,v in mp.items() if v is not None }
    ga_out, DO = om.run_ga(mp ,10, local_tests, free_params = mp, NSGA = True, MU = 10, model_type = str('GLIF'))#,seed_pop=seeds[key])


    #ga_out = pickle.load(open('adexp_ca1.p','rb'))
    dtcpopad = [ ind.dtc for ind in dtcpopad[key]['pf'] ]

    #ga_out = pickle.load(open('izhi_ca1.p','rb'))    

    dtcpopiz = [ ind.dtc for ind in ga_outiz[key]['pf'] ]
    from neuronunit.optimisation.optimisation_management import inject_and_plot
    inject_and_plot(dtcpopiz[0:2],dtcpopad[0:2])

