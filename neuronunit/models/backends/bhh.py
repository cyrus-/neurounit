
import brian2 as b2
from neurodynex.hodgkin_huxley import HH
b2.defaultclock.dt = 1 * b2.ms

from neurodynex.tools import plot_tools, input_factory
import io
import math
import pdb
from numba import jit
import numpy as np
from .base import *
import quantities as qt
from quantities import mV, ms, s, us, ns
import matplotlib as mpl

from neuronunit.capabilities import spike_functions as sf
mpl.use('Agg')
import matplotlib.pyplot as plt

from types import MethodType
# from neuronunit.optimisation import ascii_plot

#import matplotlib.pyplot as plt
# @jit(cache=True) I suspect this causes a memory leak

try:
    import asciiplotlib as apl
    fig = apl.figure()
    fig.plot([0,1], [0,1], label=str('spikes: ')+str(self.n_spikes), width=100, height=20)
    fig.show()
    ascii_plot = True
except:
    ascii_plot = False
import numpy


from scipy.interpolate import interp1d

# from scipy.interpolate import interp1d

def downsample(array, npts):
    interpolated = interp1d(np.arange(len(array)), array, axis = 0, fill_value = 'extrapolate')
    downsampled = interpolated(np.linspace(0, len(array), npts))
    return downsampled

# downsampled_y = downsample(y, 6000)

class BHHBackend(Backend):
    def get_spike_count(self):
        return int(self.spike_monitor.count[0])
    def init_backend(self, attrs=None, cell_name='thembi',
                     current_src_name='spanner', DTC=None,
                     debug = False):
        backend = 'brianHH'
        super(BHHBackend,self).init_backend()
        self.name = str(backend)

        #self.threshold = -20.0*qt.mV
        self.debug = None
        self.model._backend.use_memory_cache = False
        self.current_src_name = current_src_name
        self.cell_name = cell_name
        self.vM = None
        self.attrs = attrs
        self.debug = debug
        self.temp_attrs = None
        self.n_spikes = None
        self.spike_monitor = None
        self.peak_v = 0.02
        self.verbose = False
        self.model.get_spike_count = self.get_spike_count


        if type(attrs) is not type(None):
            self.set_attrs(**attrs)
            self.sim_attrs = attrs

        if type(DTC) is not type(None):
            if type(DTC.attrs) is not type(None):
                self.set_attrs(**DTC.attrs)
            if hasattr(DTC,'current_src_name'):
                self._current_src_name = DTC.current_src_name
            if hasattr(DTC,'cell_name'):
                self.cell_name = DTC.cell_name



    def set_stop_time(self, stop_time = 650*pq.ms):
        """Sets the simulation duration
        stopTimeMs: duration in milliseconds
        """
        self.tstop = float(stop_time.rescale(pq.ms))


    def get_membrane_potential(self):
        """Must return a neo.core.AnalogSignal.
        And must destroy the hoc vectors that comprise it.
        """
        
        return self.vM

    def set_attrs(self, **attrs):

        self.HH = None
        self.HH = HH

        if len(attrs):
            '''
            # neuron parameters
            El = 10.6 * b2.mV
            EK = -12 * b2.mV
            ENa = 115 * b2.mV
            gl = 0.3 * b2.msiemens
            gK = 36 * b2.msiemens
            gNa = 120 * b2.msiemens
            C = 1 * b2.ufarad
            '''
            self.EL = attrs['El'] * b2.units.mV,
            self.EK = attrs['EK'] * b2.units.mV,
            self.ENa = attrs['ENa'] * b2.units.mV,
            self.gl =  attrs['gl'] * b2.units.msiemens,
            self.gK = attrs['gK'] * b2.units.msiemens,
            self.gNa = attrs['gNA'] * b2.units.msiemens,
            self.C = attrs['C'] * b2.units.ufarad,
            self.I_stim = stim, simulation_time=st)


            #if str('peak_v') in attrs:
            #    self.peak_v = attrs['peak_v']

            self.model.attrs.update(attrs)
        if attrs is None:
            #from neurodynex.HH_model import HH
            b2.defaultclock.dt = 1 * b2.ms

            self.HH =HH
    def finalize(self):
        '''
        Necessary for imputing missing sampling, simulating at high sample frequency is prohibitevely slow, with
        out significant difference in behavior.
        '''
        transform_function = interp1d([float(t) for t in self.vM.times],[float(v) for v in self.vM.magnitude])
        xnew = np.linspace(0, float(np.max(self.vM.times)), num=1004001, endpoint=True)
        vm_new = transform_function(xnew) #% generate the y values for all x values in xnew
        self.vM = AnalogSignal(vm_new,units = mV,sampling_period = float(xnew[1]-xnew[0]) * pq.s)
        if self.verbose:

            print(len(self.vM))
        self.vM = AnalogSignal(vm_new,units = mV,sampling_period = float(xnew[1]-xnew[0]) * pq.s)
        return self.vM
    def inject_square_current(self, current):#, section = None, debug=False):
        """Inputs: current : a dictionary with exactly three items, whose keys are: 'amplitude', 'delay', 'duration'
        Example: current = {'amplitude':float*pq.pA, 'delay':float*pq.ms, 'duration':float*pq.ms}}
        where \'pq\' is a physical unit representation, implemented by casting float values to the quanitities \'type\'.
        Description: A parameterized means of applying current injection into defined
        Currently only single section neuronal models are supported, the neurite section is understood to be simply the soma.

        """
        b2.defaultclock.dt = 1 * b2.ms
        self.state_monitor = None
        self.spike_monitor = None
        self.HH = None
        self.HH = HH
        attrs = copy.copy(self.model.attrs)
        if self.model.attrs is None or not len(self.model.attrs):
            self.HH = HH
        else:
            self.set_attrs(**attrs)
        if 'injected_square_current' in current.keys():
            c = current['injected_square_current']
        else:
            c = current
        amplitude = float(c['amplitude'])
        duration = int(c['duration'])#/dt#/dt.rescale('ms')
        delay = int(c['delay'])#/dt#.rescale('ms')
        pre_current = int(duration)+100
        try:
            stim = input_factory.get_step_current(int(delay), int(pre_current), 1 * b2.ms, amplitude *b2.pA)
        except:
            pass
        st = (duration+delay+100)* b2.ms

        if self.model.attrs is None or not len(self.model.attrs):
            #from neurodynex.HH_model import HH
            b2.defaultclock.dt = 1 * b2.ms

            self.HH = HH
            self.state_monitor, self.spike_monitor = self.HH.simulate_HH_neuron(I_stim = stim, simulation_time=st)

        else:
            if self.verbose:
                print(attrs)
            self.set_attrs(**attrs)
            self.state_monitor, self.spike_monitor = self.HH.simulate_HH_neuron(
            EL = attrs['El'] * b2.units.mV,
            EK = attrs['EK'] * b2.units.mV,
            ENa = attrs['ENa'] * b2.units.mV,
            gl =  attrs['gl'] * b2.units.msiemens,
            gK = attrs['gK'] * b2.units.msiemens,
            gNa = attrs['gNA'] * b2.units.msiemens,
            C = attrs['C'] * b2.units.ufarad,
            I_stim = stim, simulation_time=st)

        self.state_monitor.clock.dt = 1 *b2.ms
        self.dt = self.state_monitor.clock.dt

        state_dic = self.state_monitor.get_states()
        vm = state_dic['v']
        vm = [ float(i) for i in vm ]
        self.vM = AnalogSignal(vm,units = mV,sampling_period = float(1.0) * pq.ms)
        # tdic = self.spike_monitor.spike_trains()
        self.n_spikes = int(self.spike_monitor.count[0])
        self.attrs = attrs

        if ascii_plot:
            t = [float(f) for f in self.vM.times]
            v = [float(f) for f in self.vM.magnitude]
            fig = apl.figure()
            fig.plot(t, v, label=str('spikes: ')+str(self.n_spikes), width=100, height=20)
            fig.show()
            fig  = None

        if len(self.spike_monitor.spike_trains())>1:
            import matplotlib.pyplot as plt
            plt.plot(y,x)
            plt.savefig('debug.png')
        return self.vM

    def _backend_run(self):
        results = None
        results = {}

        results['vm'] = self.vM

        results['t'] = self.vM.times
        results['run_number'] = results.get('run_number',0) + 1
        return results
