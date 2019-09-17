
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.use('agg')
import logging
logging.info("test")
from allensdk.core.cell_types_cache import CellTypesCache
from allensdk.ephys.extract_cell_features import extract_cell_features
from collections import defaultdict
from neuronunit.optimisation.optimisation_management import inject_rh_and_dont_plot, add_druckmann_properties_to_cells

from allensdk.core.nwb_data_set import NwbDataSet
import pickle

from neuronunit import aibs

#dm_tests = init_dm_tests(value,1.5*value)

try:
    ctc = CellTypesCache(manifest_file='cell_types/manifest.json')
except:
    pass
    all_features = ctc.get_all_features()
    pickle.dump(all_features,open('all_features.p','wb'))

try:
    with open('../all_allen_cells.p','rb') as f:
        cells = pickle.load(f)
        #cells = pickle.load(open('../all_allen_cells.p','rb'))

except:
    ctc = CellTypesCache(manifest_file='cell_types/manifest.json')
    cells = ctc.get_cells()
    with open('all_allen_cells.p','wb') as f:
        pickle.dump(cells,f)

ids = [ c['id'] for c in cells ]



files = [324257146, 485909730]
data = []
for specimen_id in ids:
    data_set = ctc.get_ephys_data(specimen_id)

    file_name = 'cell_types/specimen_'+str(specimen_id)+'/ephys.nwb'
    data_set = NwbDataSet(file_name)
    everything = aibs.get_nwb(specimen_id)
    prefix = str('/dedicated_folder')
    try:
        os.mkdir(prefix)
    except:
        pass
    import pdb
    pdb.set_trace()
        #pass
    pickle.dump(everything,open(prefix+str(specimen_id)+'.p','wb'))



'''
import pdb; pdb.set_trace()


def a_cell_for_check(stim):
    cells = pickle.load(open("multi_objective_raw.p","rb"))

    dtc = cells['results']['RAW']['Dentate gyrus basket cell']['pf'][0].dtc
    dtc.attrs['dt'] = 0.0001

    (_,times,vm) = inject_rh_and_dont_plot(dtc)
    return (_,times,vm)
# if you ran the examples above, you will have a NWB file here

file_name = 'cell_types/specimen_485909730/ephys.nwb'
specimen_id = 485909730

try:
    data_set = NwbDataSet(file_name)
except:
    pass



def get_features(specimen_id = 485909730):
    data_set = ctc.get_ephys_data(specimen_id)
    sweeps = ctc.get_ephys_sweeps(specimen_id)
    #import pdb; pdb.set_trace()
    for s in sweeps:
        if s['ramp']:

            print([(k,v) for k,v in s.items()])
        current = {}
        current['amplitude'] = s['stimulus_absolute_amplitude']
        current['duration'] = s['stimulus_duration']
        current['delay'] = s['stimulus_start_time']


    # group the sweeps by stimulus
    sweep_numbers = defaultdict(list)
    for sweep in sweeps:
        sweep_numbers[sweep['stimulus_name']].append(sweep['sweep_number'])

    # calculate features
    cell_features = extract_cell_features(data_set,
                                          sweep_numbers['Ramp'],
                                          sweep_numbers['Short Square'],
                                          sweep_numbers['Long Square'])
'''