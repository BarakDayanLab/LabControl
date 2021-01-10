from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
import time
import numpy as np
import qm
from time import sleep

qmManager = QuantumMachinesManager()
#qmManager = QuantumMachinesManager()
#offsets = [-0.09745, 0.1144] * 2
offsets = [0, 0]  # Daniel changed this line, You can chane it back to the line above
# offsets = [-0.08232403, 0.0194166]
# offsets = [-0.08302877, 0.01893423]
# offsets = [-0.1, 0.02]
# offsets = [-0.02518957,  -0.03253227]
# offsets = [-0.02505083, -0.03288917]
offsets = [-0.01660398, -0.0576567 ]
offsets = [0.1, 0]
DC_I = offsets[0]
DC_Q = offsets[1]


port_I = 1
port_Q = 9

LO_freq = 0
f0 = LO_freq + 25e6

corvars = [2.16005713e-04, 1.4]
corvars = [-0.10308351, 0.89446135]
corvars = [-0.11507042, 0.89980469]
corvars = [0.50478125, 0.74776809]
corvars = [0, 1]
th = corvars[0]
k = corvars[1]


R = [[np.sin(th),np.cos(th)], [np.cos(th), np.sin(th)]]
c = [[k, 0], [0 , 1/k]]
M = np.dot(c, R).flatten().tolist()

with program() as prog:
    with infinite_loop_():
        play('pulse1', 'qe1')


config = {
    'version': 1,
    'controllers': {
        'con1': {
            'type': 'opx1',
            'analog_outputs': {
                port_I: {'offset': DC_I},
                port_Q: {'offset': DC_Q}
            }
        }
    },

    'elements': {
            'qe1': {
                'mixInputs': {
                   'I': ('con1', port_I),
                   'Q': ('con1', port_Q),
                   'mixer': 'my_mixer',
                   'lo_frequency': LO_freq
                 },
                'intermediate_frequency': f0,
                'operations': {
                    'pulse1': 'pulse1_in',
                }
            }
    },

    'pulses': {
        'pulse1_in': {
            'operation': 'control',
            'length': 24,
            'waveforms': {
                'I': 'wf1',
                'Q': 'wf2'
            }
        }

    },

    'waveforms': {
        'wf1': {
            'type': 'constant',
            'sample': 0.2
        },
        'wf2': {
            'type': 'constant',
            'sample': 0.2
        }

    },
    "mixers": {
        "my_mixer": [
            {"intermediate_frequency": f0, "lo_frequency": LO_freq, "correction": M}
        ]
    }

}


qm1 = qmManager.open_qm(config)
job = qm1.execute(prog)
print(job.id())
