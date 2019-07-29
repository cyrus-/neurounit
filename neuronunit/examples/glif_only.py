
# coding: utf-8

# In[1]:


from hide_imports import *


# In[2]:


with open('../gcm.p','rb') as f:
    glif_params = pickle.load(f)
#flat_iter = [ mp.pop(list(mp.keys())[0]) for mp in glif_params ]
#new_flat_iter = [(k,v) for fi in flat_iter for k,v in fi.items() ]
'''
glif_range = {}
for k,v in new_flat_iter:
    glif_range[k] = [v,v]
for k,v in new_flat_iter:
    if isinstance(v,dict) and not isinstance(v,type(None)) and not isinstance(v,list):
        if v<glif_range[k][0]:
            glif_range[k][0] = v
        if v>glif_range[k][1]:
            glif_range[k][1] = v
    else:
        glif_range[k] = v
'''
#new_flat_iter


# In[3]:


for k,v in rts.items():
    gt = {}
    gt[k] = {}    
    gt[k]['InjectedCurrentAPAmplitudeTest'] = v
    gt[k]['CapacitanceTest'] = v
    gt[k]['TimeConstantTest'] = v
    gt[k]['RheobaseTest'] = v


# In[4]:


ga_out_glif = {}
for key,v in rts.items():
    local_tests = [value for value in v.values() ]
    break
    

mp = model_params.MODEL_PARAMS['GLIF']

mp = { k:v for k,v in mp.items() if type(v) is not dict }
mp = { k:v for k,v in mp.items() if v is not None }
ga_out_glif[key], DO = om.run_ga(mp ,2, local_tests, free_params = mp, NSGA = True, MU = 4, model_type = str('GLIF'))#,seed_pop=seeds[key])


#ga_out = pickle.load(open('adexp_ca1.p','rb'))
#dtcpopad = [ ind.dtc for ind in dtcpopad[key]['pf'] ]


dtcpopiz = [ ind.dtc for ind in ga_out_glif[list(ga_out_glif.keys())[0]]['pf'] ]
from neuronunit.optimisation.optimisation_management import inject_and_plot
inject_and_plot(dtcpopiz[0:2])


# In[5]:


dtcpopiz[0].score


# In[6]:


dtcpopiz


# In[7]:


ga_out_glif[list(ga_out_glif.keys())[0]]['pf'][0].dtc.scores


# In[8]:


ga_out_glif[list(ga_out_glif.keys())[0]]['pf'][-1].dtc.scores


# In[9]:


ga_out_glif[list(ga_out_glif.keys())[0]]['pop'][0].dtc.scores


# In[10]:


model = ga_out_glif[list(ga_out_glif.keys())[0]]['pop'][0].dtc.dtc_to_model()
dtc = ga_out_glif[list(ga_out_glif.keys())[0]]['pop'][0].dtc


# In[11]:


from neuronunit.optimisation.optimisation_management import nunit_evaluation_simple
print('gets here')
import pdb
pdb.set_trace()
glif_and_score = []
for l in glif_params[0:4]:
    for value in l.values():
        for k,v in model.attrs.items():
            dtc.attrs[k] = value[k]
            model.attrs[k] = value[k]
            for test in dtc.tests:
                test.judge(model)
        score = nunit_evaluation_simple(dtc)
        glif_and_score.append(dtc.scores)


# In[12]:


for g in glif_and_score: print(g)


# In[13]:


type(new_flat_iter)
np.shape(new_flat_iter)


# In[ ]:


glif_params[1]


# In[ ]:


glif_params


# In[ ]:


with open('../gcm.p','rb') as f:
    glif_params = pickle.load(f)


# In[ ]:


glif_params[0]

