from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
import MWSpectroscopy.configurations as configurations
import json
import sys
import logging
from logging import StreamHandler, Formatter, INFO, WARN, ERROR

logger = logging.getLogger("MWSpectroscopy")
logger.setLevel(INFO)
handler = StreamHandler(sys.stdout)
handler.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class MWSpectroscopy:

    def __init__(self, conf_args_path):
        with open(conf_args_path, 'r') as fp:
            self.conf_args = json.load(fp)
        self.qmconf = configurations.create_config(**self.conf_args)
        self.qmManager = QuantumMachinesManager()
        self.qm1 = self.qmManager.open_qm(self.qmconf)
        self.job = None
        # initializing the DC values by playing a short pulse with loaded configurations
        with program() as initialize_prog:
            zero = declare(fixed, value=0)
            play('pulse1'*amp(zero), 'antena1')
        self.qm1.execute(initialize_prog)
        logger.info('quantum machine initialized')

    def __del__(self):
        # self.job.halt()
        self.qm1.close()
        self.qmManager.close()

    def square_pulse(self, im_freq, duration=None):
        with program() as prog:
            update_frequency('antena1', int(im_freq))
            play('pulse1', 'antena1', duration)

        self.job = self.qm1.execute(prog, force_execution=True)

    def infinite_pulse(self, im_freq):
        with program() as prog:
            update_frequency('antena1', int(im_freq))
            with infinite_loop_():
                play('pulse1', 'antena1')

        self.job = self.qm1.execute(prog, force_execution=True)

    @staticmethod
    def calibrate(config_args_path=None):
        import MWSpectroscopy.calibration as calibration
        calibration.optimize(config_args_path)


def main():
    with open('conf_args.json', 'r') as fp:
        conf_args = json.load(fp)
    myconf = configurations.create_config(**conf_args)
    prog = qua_program(34e6)
    qmManager = QuantumMachinesManager()
    qm1 = qmManager.open_qm(myconf)
    job = qm1.execute(prog, forceExecution=True)
    qm1.close()
    qmManager.close()
    return


def qua_program(im_freq, duration=None):
    with program() as prog:
        #play(pulse, 'antena1', duration)
        update_frequency('antena1', int(im_freq))
        with infinite_loop_():
            play('pulse1', 'antena1', duration)

    return prog

