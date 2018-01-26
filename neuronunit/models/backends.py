"""Simulator backends for NeuronUnit models"""
import sys
import os
import platform
import re
import copy
import tempfile
import pickle
import importlib
import shelve
import subprocess

import neuronunit.capabilities as cap
from quantities import ms, mV, nA
from pyneuroml import pynml
from quantities import ms, mV
from neo.core import AnalogSignal
import neuronunit.capabilities.spike_functions as sf
import sciunit
from sciunit.utils import dict_hash, import_module_from_path
try:
    import neuron
    from neuron import h
    NEURON_SUPPORT = True
except:
    NEURON_SUPPORT = False


class Backend(object):
    """Base class for simulator backends that implement simulator-specific
    details of modifying, running, and reading results from the simulation
    """

    def init_backend(self, *args, **kwargs):
        self.model.attrs = {}

        self.use_memory_cache = kwargs.get('use_memory_cache', True)
        if self.use_memory_cache:
            self.init_memory_cache()
        self.use_disk_cache = kwargs.get('use_disk_cache', False)
        if self.use_disk_cache:
            self.init_disk_cache()
        self.load_model()
        self.model.unpicklable += ['_backend']

    # Name of the backend
    backend = None

    #The function (e.g. from pynml) that handles running the simulation
    f = None

    def init_cache(self):
        self.init_memory_cache()
        self.init_disk_cache()

    def init_memory_cache(self):
        self.memory_cache = {}

    def init_disk_cache(self):
        try:
            # Cleanup old disk cache files
            path = self.disk_cache_location
            os.remove(path)
        except:
            pass
        self.disk_cache_location = os.path.join(tempfile.mkdtemp(),'cache')

    def get_memory_cache(self, key):
        """Returns result in memory cache for key 'key' or None if it
        is not found"""
        self._results = self.memory_cache.get(key)
        return self._results

    def get_disk_cache(self, key):
        """Returns result in disk cache for key 'key' or None if it
        is not found"""
        if not getattr(self,'disk_cache_location',False):
            self.init_disk_cache()
        disk_cache = shelve.open(self.disk_cache_location)
        self._results = disk_cache.get(key)
        disk_cache.close()
        return self._results

    def set_memory_cache(self, results, key=None):
        """Stores result in memory cache with key
        corresponding to model state"""
        key = self.model.hash if key is None else key
        self.memory_cache[key] = results

    def set_disk_cache(self, results, key=None):
        """Stores result in disk cache with key
        corresponding to model state"""
        if not getattr(self,'disk_cache_location',False):
            self.init_disk_cache()
        disk_cache = shelve.open(self.disk_cache_location)
        key = self.model.hash if key is None else key
        disk_cache[key] = results
        disk_cache.close()

    def set_attrs(self, **attrs):
        """Set model attributes, e.g. input resistance of a cell"""
        #If the key is in the dictionary, it updates the key with the new value.
        self.model.attrs.update(attrs)
        #pass

    def set_run_params(self, **params):
        """Set run-time parameters, e.g. the somatic current to inject"""
        self.model.run_params.update(params)
        self.check_run_params()
        #pass

    def check_run_params(self):
        """Check to see if the run parameters are reasonable for this model
        class.  Raise a sciunit.BadParameterValueError if any of them are not.
        """
        pass

    def load_model(self):
        """Load the model into memory"""
        pass

    def local_run(self):
        """Checks for cached results in memory and on disk, then runs the model
        if needed"""
        key = self.model.hash
        if self.use_memory_cache and self.get_memory_cache(key):
            return self._results
        if self.use_disk_cache and self.get_disk_cache(key):
            return self._results
        results = self._local_run()
        if self.use_memory_cache:
            self.set_memory_cache(results, key)
        if self.use_disk_cache:
            self.set_disk_cache(results, key)
        return results

    def _local_run(self):
        """Runs the model via the backend"""
        raise NotImplementedError("Each backend must implement '_local_run'")

    def save_results(self, path='.'):
        with open(path,'wb') as f:
            pickle.dump(self.results,f)


class BackendException(Exception):
    pass


class jNeuroMLBackend(Backend):
    """Used for simulation with jNeuroML, a reference simulator for NeuroML"""

    backend = 'jNeuroML'

    def init_backend(self, *args, **kwargs):
        self.model.create_lems_file_copy()
        super(jNeuroMLBackend,self).init_backend(*args, **kwargs)

    def set_attrs(self, **attrs):
        self.model.attrs.update(attrs)
        self.model.set_lems_attrs(attrs)

    def set_run_params(self, **params):
        super(jNeuroMLBackend,self).set_run_params(**params)
        self.model.set_lems_run_params()

    def inject_square_current(self, current):
        self.set_run_params(injected_square_current=current)

    def _local_run(self):
        f = pynml.run_lems_with_jneuroml
        self.exec_in_dir = tempfile.mkdtemp()
        results = f(self.model.lems_file_path,
                    include=[os.path.dirname(self.model.orig_lems_file_path)],
                    skip_run=self.model.skip_run,
                    nogui=self.model.run_params['nogui'],
                    load_saved_data=True, plot=False,
                    exec_in_dir=self.exec_in_dir,
                    verbose=self.model.run_params['v'])
        return results


class NEURONBackend(Backend):
    """Used for simulation with NEURON, a popular simulator
    http://www.neuron.yale.edu/neuron/
    Units used by NEURON are sometimes different to quantities/neo
    (note nA versus pA)
    http://neurosimlab.org/ramcd/pyhelp/modelspec/programmatic/mechanisms/mech.html#IClamp
    NEURON's units:
    del -- ms
    dur -- ms
    amp -- nA
    i -- nA
    """

    def init_backend(self, attrs = None, cell_name = None, current_src_name = None, DTC = None):
        '''Initialize the NEURON backend for neuronunit.
        Optional Key Word Arguments:
        Arguments: attrs a dictionary of items used to update NEURON model attributes.
        cell_name, and _current_src_name should not attain arbitrary values, rather these variable names
        may need to have consistency with an underlying jNEUROML model files:
        LEMS_2007One_nrn.py  LEMS_2007One.xml
        cell_name: A string that represents the cell models name in the NEURON HOC space.
        current_src_name: A string that represents the current source models name in the NEURON HOC space.
        DTC: An object of type Data Transport Container. The data transport container contains a dictionary of model attributes
        When the DTC object is provided, it\'s attribute dictionary can be used to update the NEURONBackends model attribute dictionary.
        '''
        if not NEURON_SUPPORT:
            raise BackendException("The neuron module was not successfully imported")


        self.neuron = None
        self.model_path = None
        self.h = h
        # Should check if a legitimately parallel MPI based NEURON is supported.

        # Are these NEURON imports really necessary?
        # self.h.load_file("stdlib.hoc")
        # self.h.load_file("stdgui.hoc")
        self.lookup = {}

        super(NEURONBackend,self).init_backend()
        self.model.unpicklable += ['h','ns','_backend']
        if cell_name:
            self._cell_name = cell_name
        if current_src_name:
            self._current_src_name = current_src_name
        '''
        if DTC is not None:
            self.model.set_attrs(DTC.attrs)

        if type(DTC) is not type(None):
            self.set_attrs(**DTC.attrs)
            if type(DTC.rheobase) is not type(None):
                self.model.rheobase = DTC.rheobase
            else:
                self.model.rheobase = None
        '''
    backend = 'NEURON'

    def reset_neuron(self, neuronVar):
        """Arguments: neuronVar, the neuronmodules path in the current python namespace.
        Side effects: refreshes the the HOC module, purging it's variable namespace.

        Sets the NEURON h variable, and resets the NEURON h variable.
        The NEURON h variable, may benefit from being reset between simulation runs
        as a way of insuring that each simulation is freshly initialized.
        the reset_neuron method is used to prevent a situation where a new models
        initial conditions are erroneously updated from a stale models final state.
        """
        #self.h = None

        self.h = neuronVar.h
        self.neuron = neuronVar



    def set_stop_time(self, stopTime = 500*ms):
        """Sets the simulation duration
        stopTimeMs: duration in milliseconds
        """

        tstop = stopTime
        tstop.units = ms
        self.h.tstop = float(tstop)

    def set_time_step(self, integrationTimeStep = 1/128.0 * ms):
        """Sets the simulation itegration fixed time step
        integrationTimeStepMs: time step in milliseconds.
        Powers of two preferred. Defaults to 1/128.0
        """

        dt = integrationTimeStep
        dt.units = ms
        self.h.dt = self.fixedTimeStep = float(dt)

    def set_tolerance(self, tolerance = 0.001):
        """Sets the variable time step integration method absolute tolerance.
        tolerance: absolute tolerance value
        """

        self.h.cvode.atol(tolerance)

    def set_integration_method(self, method = "fixed"):
        """Sets the simulation itegration method
        method: either "fixed" or "variable". Defaults to fixed.
        cvode is used when "variable" """

        # This line is compatible with the above cvodes
        # statements.
        self.h.cvode.active(1 if method == "variable" else 0)

        try:
            assert self.cvode.active()
        except:
            self.cvode = self.h.CVode()
            self.cvode.active(1 if method == "variable" else 0)

    def get_membrane_potential(self):
        """Must return a neo.core.AnalogSignal.
        And must destroy the hoc vectors that comprise it.
        """

        if self.h.cvode.active() == 0:
            dt = float(copy.copy(self.h.dt))
            fixed_signal = copy.copy(self.vVector.to_python())
        else:
            dt = float(copy.copy(self.fixedTimeStep))
            fixed_signal =copy.copy(self.get_variable_step_analog_signal())

        self.h.dt = dt
        self.fixedTimeStep = float(1.0/dt)
        return AnalogSignal(fixed_signal,
                            units = mV,
                            sampling_period = dt * ms)

    def get_variable_step_analog_signal(self):
        """Converts variable dt array values to fixed
        dt array by using linear interpolation"""

        # Fixed dt potential
        fPots = []
        fDt = self.fixedTimeStep
        # Variable dt potential
        vPots = self.vVector.to_python()
        # Variable dt times
        vTimes = self.tVector.to_python()
        duration = vTimes[len(vTimes)-1]
        # Fixed and Variable dt times
        fTime = vTime = vTimes[0]
        # Index of variable dt time array
        vIndex = 0
        # Advance the fixed dt position
        while fTime <= duration:

            # If v and f times are exact, no interpolation needed
            if fTime == vTime:
                fPots.append(vPots[vIndex])

            # Interpolate between the two nearest vdt times
            else:

                # Increment vdt time until it surpases the fdt time
                while fTime > vTime and vIndex < len(vTimes):
                    vIndex += 1
                    vTime = vTimes[vIndex]

                # Once surpassed, use the new vdt time and t-1 for interpolation
                vIndexMinus1 = max(0, vIndex-1)
                vTimeMinus1 = vTimes[vIndexMinus1]

                fPot = self.linearInterpolate(vTimeMinus1, vTime, \
                                          vPots[vIndexMinus1], vPots[vIndex], \
                                          fTime)

                fPots.append(fPot)

            # Go to the next fdt time step
            fTime += fDt

        return fPots

    def linearInterpolate(self, tStart, tEnd, vStart, vEnd, tTarget):
        tRange = float(tEnd - tStart)
        tFractionAlong = (tTarget - tStart)/tRange
        vRange = vEnd - vStart
        vTarget = vRange*tFractionAlong + vStart

        return vTarget

    def load(self):
        nrn_path = os.path.splitext(self.model.orig_lems_file_path)[0]+'_nrn.py'
        nrn = import_module_from_path(nrn_path)
        self.reset_neuron(nrn.neuron)
        modeldirname = os.path.dirname(self.model.orig_lems_file_path)
        self.set_stop_time(650*ms) # previously 500ms add on 150ms of recovery
        self.h.tstop
        self.ns = nrn.NeuronSimulation(self.h.tstop, dt=0.0025)

    def load_mechanisms(self):
        neuron.load_mechanisms(self.neuron_model_dir)

    def load_model(self, verbose=True):
        """Inputs: NEURONBackend instance object
        Side Effects: Substantially mutates neuronal model stored in self.
        Description: Take a declarative model description, and call JneuroML to convert it
        into an python/neuron implementation stored in a pyhoc file.
        Then import the pyhoc file thus dragging the neuron variables
        into memory/python name space.
        Since this only happens once outside of the optimization
        loop its a tolerable performance hit.
        """

        #Create a pyhoc file using jneuroml to convert from NeuroML to pyhoc.
        #import the contents of the file into the current names space.

        #The code block below does not actually function:
        #architecture = platform.machine()
        assert os.path.isfile(self.model.orig_lems_file_path)
        base_name = os.path.splitext(self.model.orig_lems_file_path)[0]
        NEURON_file_path ='{0}_nrn.py'.format(base_name)
        self.neuron_model_dir = os.path.dirname(self.model.orig_lems_file_path)
        assert os.path.isdir(self.neuron_model_dir)
        if not os.path.exists(NEURON_file_path):
            pynml.run_lems_with_jneuroml_neuron(self.model.orig_lems_file_path,
                              skip_run=False,
                              nogui=True,
                              load_saved_data=False,
                              only_generate_scripts=True,
                              plot=False,
                              show_plot_already=False,
                              exec_in_dir = self.neuron_model_dir,
                              verbose=True,
                              exit_on_fail = True)
            # use a different process to call NEURONS compiler nrnivmodl in the
            # background if the NEURON_file_path does not yet exist.
            subprocess.run(["cd %s; nrnivmodl" % self.neuron_model_dir],shell=True)
            self.load_mechanisms()
        elif os.path.realpath(os.getcwd()) != os.path.realpath(self.neuron_model_dir):
            # Load mechanisms unless they've already been loaded
            self.load_mechanisms()

        self.load()


        # Although the above approach successfuly instantiates a LEMS/neuroml model in pyhoc
        # the resulting hoc variables for current source and cell name are idiosyncratic (not generic).
        # the non generic approach described above makes it hard to create a generalizable code.
        # work around involves predicting the hoc variable names from pyneuroml LEMS file that was used to generate them.
        more_attributes = pynml.read_lems_file(self.model.orig_lems_file_path,
                                               include_includes=True,
                                               debug=False)
        for i in more_attributes.components:
            # This code strips out simulation parameters from the xml tree also such as current source name.
            # and cell_name
            if str('pulseGenerator') in i.type:
                self._current_src_name = i.id
            if str('Cell') in i.type:
                self._cell_name = i.id
        more_attributes = None # explitly perform garbage collection on more_attributes since its not needed anymore.
        return self

    @property
    def cell_name(self):
        return getattr(self,'_cell_name','RS')

    @property
    def current_src_name(self):
        return getattr(self,'_current_src_name','RS')

    def set_attrs(self, **attrs):
        self.model.attrs.update(attrs)
        assert type(self.model.attrs) is not type(None)
        assert len(list(self.model.attrs.values())) > 0
        for h_key,h_value in attrs.items():
            self.h('m_{0}_{1}_pop[0].{2} = {3}'\
                .format(self.cell_name,self.cell_name,h_key,h_value))

        # Below create a list of NEURON experimental recording rig parameters.
        # This is where parameters of the artificial neuron experiment are initiated.
        # Code is sent to the python interface to neuron by executing strings:
        neuron_sim_rig = []
        neuron_sim_rig.append(' { v_time = new Vector() } ')
        neuron_sim_rig.append(' { v_time.record(&t) } ')
        neuron_sim_rig.append(' { v_v_of0 = new Vector() } ')
        neuron_sim_rig.append(' { v_v_of0.record(&RS_pop[0].v(0.5)) } ')
        neuron_sim_rig.append(' { v_u_of0 = new Vector() } ')
        neuron_sim_rig.append(' { v_u_of0.record(&m_RS_RS_pop[0].u) } ')

        for string in neuron_sim_rig:
            # execute hoc code strings in the python interface to neuron.
            self.h(string)

        # These two variables have been aliased in the code below:
        self.tVector = self.h.v_time
        self.vVector = self.h.v_v_of0

        return self

    def inject_square_current(self, current, section = None):
        """Inputs: current : a dictionary with exactly three items, whose keys are: 'amplitude', 'delay', 'duration'
        Example: current = {'amplitude':float*pq.pA, 'delay':float*pq.ms, 'duration':float*pq.ms}}
        where \'pq\' is a physical unit representation, implemented by casting float values to the quanitities \'type\'.
        Description: A parameterized means of applying current injection into defined
        Currently only single section neuronal models are supported, the neurite section is understood to be simply the soma.

        Implementation:
        1. purge the HOC space, by calling reset_neuron()
        2. Redefine the neuronal model in the HOC namespace, which was recently cleared out.
        3. Strip away quantities representation of physical units.
        4. Translate the dictionary of current injection parameters into executable HOC code.


        """
        self.h = None
        self.neuron = None

        #import neuron
        nrn_path = os.path.splitext(self.model.orig_lems_file_path)[0]+'_nrn.py'
        nrn = import_module_from_path(nrn_path)
        import copy
        cache_attrs = copy.copy(self.model.attrs)
        self.init_backend()
        self.set_attrs(**cache_attrs)
        #print(len(self.results))

        c = copy.copy(current)
        if 'injected_square_current' in c.keys():
            c = current['injected_square_current']

        c['delay'] = re.sub('\ ms$', '', str(c['delay'])) # take delay
        c['duration'] = re.sub('\ ms$', '', str(c['duration']))
        c['amplitude'] = re.sub('\ pA$', '', str(c['amplitude']))
        # NEURONs default unit multiplier for current injection values is nano amps.
        # to make sure that pico amps are not erroneously interpreted as a larger nano amp.
        # current injection value, the value is divided by 1000.
        amps=float(c['amplitude'])/1000.0 #This is the right scale.
        prefix = 'explicitInput_%s%s_pop0.' % (self.current_src_name,self.cell_name)
        define_current = []
        define_current.append(prefix+'amplitude=%s'%amps)
        define_current.append(prefix+'duration=%s'%c['duration'])
        define_current.append(prefix+'delay=%s'%c['delay'])
        for string in define_current:
            # execute hoc code strings in the python interface to neuron.
            self.h(string)


    def _local_run(self):
        self.h('run()')

        results={}

        # Prepare NEURON vectors for quantities/sciunit
        # By rescaling voltage to milli volts, and time to milli seconds.
        results['vm'] = [float(x/1000.0) for x in copy.copy(self.neuron.h.v_v_of0.to_python())]
        results['t'] = [float(x/1000.0) for x in copy.copy(self.neuron.h.v_time.to_python())]
        results['run_number'] = results.get('run_number',0) + 1

        return results

from neuronunit.models import section_extension
