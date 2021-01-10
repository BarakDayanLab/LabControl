import numpy as np


def default_config_args():
    def_conf = {
        'ports': {'I': 7,
                  'Q': 8},
        'offsets': {'I': 0,
                    'Q': 0},
        'correction_vars': {'theta': 0,
                            'k': 1},
        'lo_frequency': 6.8e9,
        'im_frequency': 34e6,
        'wf_samples': {'wf1': 0.01,
                       'wf2': 0.01},
        'pulse_time': 500
    }
    return def_conf


def create_config(**confargs):

    dc_i = confargs['offsets']['I']
    dc_q = confargs['offsets']['Q']
    i_port = confargs['ports']['I']
    q_port = confargs['ports']['Q']
    lo_freq = confargs['lo_frequency']
    im_freq = confargs['im_frequency']
    wf_samples = [confargs['wf_samples']['wf1'], confargs['wf_samples']['wf2']]
    correction_matrix = calc_cmat([confargs['correction_vars']['theta'], confargs['correction_vars']['k']])
    pulse_time = confargs['pulse_time']

    config = {
        'version': 1,
        'controllers': {
            'con1': {
                'type': 'opx1',
                'analog_outputs': {
                    i_port: {'offset': dc_i},
                    q_port: {'offset': dc_q}
                }
            }
        },

        'elements': {
            'antena1': {
                'mixInputs': {
                    'I': ('con1', i_port),
                    'Q': ('con1', q_port),
                    'mixer': 'my_mixer',
                    'lo_frequency': lo_freq
                },
                'intermediate_frequency': im_freq,
                'operations': {
                    'pulse1': 'pulse1_in',
                }
            }
        },

        'pulses': {
            'pulse1_in': {
                'operation': 'control',
                'length': pulse_time,
                'waveforms': {
                    'I': 'wf1',
                    'Q': 'wf2'
                }
            }

        },

        'waveforms': {
            'wf1': {
                'type': 'constant',
                'sample': wf_samples[0]
            },
            'wf2': {
                'type': 'constant',
                'sample': wf_samples[1]
            }

        },
        "mixers": {
            "my_mixer": [
                {"intermediate_frequency": im_freq, "lo_frequency": lo_freq, "correction": correction_matrix}
            ]
        }
    }
    return config


def calc_cmat(correction_vars):
    """
    calculating the correction matrix required for IQ mixer using the variable \theta   k
    :param correction_vars: array of correction variables
    theta = correction_vars[0]
    theta = correction_vars[1]
    :return: correction matrix
    """

    theta = correction_vars[0]
    k = correction_vars[1]
    R = [[np.sin(theta), np.cos(theta)], [np.cos(theta), np.sin(theta)]]
    c = [[k, 0], [0, 1 / k]]
    return np.matmul(c, R).flatten().tolist()

