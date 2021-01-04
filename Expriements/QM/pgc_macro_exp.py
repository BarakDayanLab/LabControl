# from Config_exp import Config_exp
import Config_exp
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import numpy as np
from scipy import signal


def MOT(mot_repetitions):
# The MOT function is used to play the MOT. To that end, we send RF signal to AOM_0, AOM_+, AOM_- for the duration of the MOT.
# The function uses mot_repetitions, which is derived from the MOT duration, and is calculated in the Experiment parameters section.

    ## Back to the MOT frequency ##
    update_frequency("AOM_TOP_1", Config_exp.IF_TOP1_MOT)

    ## MOT build-up: ##
    play("MOT", "MOT_AOM_0")
    play("MOT" * amp(0.89), "MOT_AOM_+")
    play("MOT", "MOT_AOM_-")
    play("Repump", "AOM_1-2'")

    n = declare(int)
    with for_(n, 1, n < mot_repetitions, n+1):
        wait(int(Config_exp.MOT_pulse_len / 4), "MOT_AOM_0", "MOT_AOM_+", "MOT_AOM_-", "AOM_1-2'")


def PGC(pgc_repetitions, da, df_pgc, df_repump, da_exp, final_amp):
# This function is used to generate PGC. To that end, a change to the MOT beams intensity as well as their frequency is needed.
# Moreover, the magnetic field must be turned off and thus the current to the Anti-Helmholtz coils is switched off.
# The change is done gradually, through entire span of the PGC duration.
# Thus, the function uses the following parameters:
#       1. pgc_repetitions - which is derived from the PGC duration.
#       2. da - which is derived from the final amplitude of the RF signals to the MOT AOMs which in turn control the MOT Beams intensity.
#       3. df_pgc - which is derived from the final frequency of the RF signal to the AOM lock of TOP 1, which in turn control the MOT Beams frequency.
#       4. df_repump - which is derived from the final frequency of the RF signal to the AOM 1-2' of the Repump, which in turn control the Repump Beam frequency.
# These parameters are calculated in the Experiment parameters section.

    ## Changing the parameters for the different AOMs. (Qua) ##
    # n = declare(int)
    # with for_(n, 1, n <= pgc_repetitions, n + 1):
    #     update_frequency("AOM_TOP_1",  Config_exp.IF_TOP1_MOT + n * df_pgc)
    #     update_frequency("AOM_1-2'", Config_exp.IF_AOM_Repump + n * df_repump)
    #     play("PGC" * amp(da), "MOT_AOM_0")
    #     play("PGC" * amp(da*0.89), "MOT_AOM_+")
    #     play("PGC" * amp(da), "MOT_AOM_-")

    da0 = declare(fixed)
    da1 = declare(fixed)
    da2 = declare(fixed)

    exp_diff_vec = declare(fixed, value=da_exp)
    n = declare(int)
    with for_(n, 0, n < pgc_repetitions, n + 1):
        update_frequency("AOM_TOP_1",  Config_exp.IF_TOP1_MOT + n * df_pgc)
        update_frequency("AOM_1-2'", Config_exp.IF_AOM_Repump + n * df_repump)
        assign(da0, exp_diff_vec[n] * (1 - final_amp))
        assign(da1, exp_diff_vec[n] * (1 - final_amp) * 0.89)
        assign(da2, exp_diff_vec[n] * (1 - final_amp))
        play("PGC" * amp(da0), "MOT_AOM_0")
        play("PGC" * amp(da1), "MOT_AOM_+")
        play("PGC" * amp(da2), "MOT_AOM_-")


def FreeFall(freefall_duration, coils_timing):
# The FreeFall function is used to stop the MOT beams and start "free-fall" section of the experiment.
# The function uses the freefall_duration and coil_timings for the purpose of turning on the Zeeman coils needed for the super-sprint experiment.

    ## Stop MOT beams ##
    ramp_to_zero("MOT_AOM_0")
    ramp_to_zero("MOT_AOM_+")
    ramp_to_zero("MOT_AOM_-")
    ramp_to_zero("AOM_1-2'")

    ## Aligning all the different elements used during the freefall time of the experiment ##
    align("MOT_AOM_0", "MOT_AOM_+", "MOT_AOM_-", "AOM_1-2'", "Zeeman_Coils", "Camera")

    ## Zeeman Coils turn-on sequence ##
    wait(int(coils_timing * 1e6 / 4), "Zeeman_Coils")
    play("ZeemanSplit", "Zeeman_Coils", duration=((freefall_duration - coils_timing) * 1e6 / 4))


def Imaging(snap_time, trig_delay):
# The Imaging function is used to flash the Rb atoms with the MOT beams as well as send a trigger to the camera at
# the right moment to get the snapshot of the Rb gas cloud that we want.
# The function gets the desired snap time and send the trigger to the camera and play the MOT beams that act as a "flash".

    ## Update to resonance frequency for flash ##
    update_frequency("AOM_TOP_1", Config_exp.IF_TOP1_Flash)

    ## Trigger ##
    wait(snap_time + trig_delay, "Camera")
    play("Snapshot", "Camera", duration=int(20 * 1e3 / 4))

    ## Flash ##
    wait(snap_time, "MOT_AOM_0", "MOT_AOM_+", "MOT_AOM_-", "AOM_1-2'")
    play("MOT", "MOT_AOM_0", duration=int(0.3 * 1e6 / 4))
    play("MOT", "MOT_AOM_+", duration=int(0.3 * 1e6 / 4))
    play("MOT", "MOT_AOM_-", duration=int(0.3 * 1e6 / 4))
    play("Repump", "AOM_1-2'", duration=int(0.3 * 1e6 / 4))
    ramp_to_zero("MOT_AOM_0")
    ramp_to_zero("MOT_AOM_+")
    ramp_to_zero("MOT_AOM_-")
    ramp_to_zero("AOM_1-2'")

    ## Back to the MOT frequency ##
    update_frequency("AOM_TOP_1", Config_exp.IF_TOP1_MOT)


def TurnOffMOT():
# The TurnOffMOT is used as the name suggests to turn OFF all the RF signals to the different AOMs in the system.

    ramp_to_zero("MOT_AOM_0")
    ramp_to_zero("MOT_AOM_+")
    ramp_to_zero("MOT_AOM_-")
    ramp_to_zero("AOM_1-2'")
    ramp_to_zero("AOM_TOP_1")


def pgc_cal_macro(qm, mot_repetitions, pgc_duration, pgc_repetitions, da, df_pgc, df_repump, freefall_duration, coils_timing, snap_time, trig_delay, da_exp, pgc_final_amp):

    with program() as pgc_cal_prog:

        i = declare(int)
        Snap_time = declare(int, value=snap_time)
        Trig_delay = declare(int, value=trig_delay)
        dA = declare(fixed, value=da)
        PGC_final_amp = declare(fixed, value=pgc_final_amp)
        df_PGC = declare(int, value=df_pgc)
        Roll = declare(bool, value=False)
        N_Snaps = declare(int, values=1)
        k = declare(int)
        assign(IO1, 0)
        assign(IO2, 0)
        play("MOT", "AOM_TOP_1")
        with infinite_loop_():
            assign(i, IO1)
            ## If we want to take images ##
            with if_((i > 0) | Roll):

                with if_((i == 1)): # Live control of the snap time
                    assign(Snap_time, IO2)
                    assign(IO1, 0)
                with if_(i == 6): # Live control on the camera trigger delay compared to the flash (can be negative)
                    assign(Trig_delay, IO2)
                    assign(IO1, 0)
                with if_(i == 2): # Live control over the final amplitude of the PGC
                    assign(PGC_final_amp, IO2)
                    assign(IO1, 0)
                with if_(i == 3): # Live control over the final frequency of the PGC beams
                    assign(df_PGC, IO2)
                    assign(IO1, 0)
                with if_(i == 4): # Turn on camera roll (taking images after each cycle)
                    assign(Roll, IO2)
                    assign(IO1, 0)
                with if_(i == 5): # Turning MOT beams off
                    with while_(IO1 == 5):
                        TurnOffMOT()
                    play("MOT", "AOM_TOP_1")
                with if_(i == 7): # Taking background image for substraction
                    assign(IO1, 0)
                    n = declare(int)
                    with for_(n, 1, n <= mot_repetitions, n + 1):
                        wait(int(Config_exp.MOT_pulse_len / 4), "MOT_AOM_0", "MOT_AOM_+", "MOT_AOM_-", "AOM_1-2'")
                    # Turning OFF anti-Helmholtz coils #
                    align("MOT_AOM_0", "MOT_AOM_+", "MOT_AOM_-", "AOM_1-2'", "AntiHelmholtz_Coils")
                    play("AntiHelmholtz_MOT", "AntiHelmholtz_Coils",
                         duration=int((pgc_duration + freefall_duration) * 1e6 / 4))
                    ####################################
                    Imaging(Snap_time, Trig_delay)
                with if_(i == 8): # Changing the number of snaps per roll, which are taken in different snap time
                    assign(N_Snaps, IO2)
                    assign(IO1, 0)

                with for_(k, 1, k <= N_Snaps, k + 1):
                    MOT(mot_repetitions)
                    # Turning OFF anti-Helmholtz coils #
                    align("MOT_AOM_0", "MOT_AOM_+", "MOT_AOM_-", "AOM_1-2'", "AntiHelmholtz_Coils")
                    play("AntiHelmholtz_MOT", "AntiHelmholtz_Coils",
                         duration=int((pgc_duration + freefall_duration) * 1e6 / 4))
                    ####################################
                    PGC(pgc_repetitions, dA, df_PGC, df_repump, da_exp, PGC_final_amp)
                    FreeFall(freefall_duration, coils_timing)
                    Imaging(Snap_time * k, Trig_delay)
                assign(N_Snaps, 1)
            ## If we don't want to take images ##
            with else_():
                MOT(mot_repetitions)
                # Turning OFF anti-Helmholtz coils #
                align("MOT_AOM_0", "MOT_AOM_+", "MOT_AOM_-", "AOM_1-2'", "AntiHelmholtz_Coils")
                play("AntiHelmholtz_MOT", "AntiHelmholtz_Coils",
                     duration=int((pgc_duration + freefall_duration) * 1e6) / 4)
                ####################################
                PGC(pgc_repetitions, dA, df_PGC, df_repump, da_exp, PGC_final_amp)
                FreeFall(freefall_duration, coils_timing)

    job = qm.execute(pgc_cal_prog)
    return job


class pgc:
    def __init__(self, config = Config_exp.config):

        ##########################
        # EXPERIMENT PARAMETERS: #
        ##########################

        # MOT parameters:
        self.MOT_duration = 2000 # [msec]

        self.MOT_Repetitions = int((self.MOT_duration * 1e6 - Config_exp.MOT_pulse_len) / Config_exp.MOT_pulse_len)

        # PGC parameters:
        self.PGC_duration = 1 # [msec]
        self.PGC_final_amp = 0.25 # Relative AOM amplitude between 0 to 1. *Last known*
        self.Repump_PGC_freq = 80e6 # The final frequency of the Repump in the PGC sequence

        self.PGC_Repetitions = int(self.PGC_duration * 1e6 / (Config_exp.PGC_pulse_len + 280))
        df_Repump = int((Config_exp.IF_AOM_Repump - self.Repump_PGC_freq) / self.PGC_Repetitions)
        dA = float((self.PGC_final_amp - 1.0) / self.PGC_Repetitions)
        tau = -(self.PGC_Repetitions - 1) / np.log(0.01)
        dA_exp = [float(arg) for arg in np.diff(signal.exponential(self.PGC_Repetitions+1, 0, tau, False))]
        df_PGC = int((Config_exp.IF_TOP1_PGC - Config_exp.IF_TOP1_MOT) / self.PGC_Repetitions)

        # Free-Fall parameters:
        # The time take the atoms to reach the Toroids and fall back = 2 * sqrt(2 * (Toroid height[m] - MOT height[m]) / g[m/sec^2]) * 1e3[msec]
        self.FreeFall_duration = 1.45 * np.sqrt(2 * 0.01 / 9.8) * 1e3 # We use 1.45 because there is a limit for the pulse duration.
        self.Coil_timing = 10 # Zeeman coils turn on time from start of free fall[msec]

        # Imaging parameters:
        self.Snapshot_Intervals = 1 # [msec]
        self.Trigger_delay = 0 # [msec]

        self.Snap_time = int(self.Snapshot_Intervals * 1e6 / 4)
        self.Trig_delay = int(self.Trigger_delay * 1e6 / 4)

        self.qmm = QuantumMachinesManager()
        self.qm = self.qmm.open_qm(config)
        self.job = pgc_cal_macro(self.qm, self.MOT_Repetitions, self.PGC_duration, self.PGC_Repetitions, dA, df_PGC,
                                 df_Repump, self.FreeFall_duration, self.Coil_timing, self.Snap_time, self.Trig_delay,
                                 dA_exp, self.PGC_final_amp)

    def update_snap_time(self, snap_time):
        self.qm.set_io_values(1, int(snap_time * 1e6 / 4))

    def update_camera_trig_time(self, trig_delay):
        self.qm.set_io_values(6, int(trig_delay * 1e6 / 4))

    def update_pgc_final_amplitude(self, final_amplitude):
        self.qm.set_io_values(2, float(final_amplitude))

    def update_df_pgc(self, pgc_final_freq):
        df_pgc = int((pgc_final_freq - Config_exp.IF_TOP1_MOT) / self.PGC_Repetitions)
        self.qm.set_io_values(3, df_pgc)

    def toggle_camera_roll(self, v):
        self.qm.set_io_values(4, v)

    def MOT_off(self):
        self.qm.set_io1_value(5)

    def MOT_on(self): # Not working
        self.qm.set_io1_value(0)

    def snap(self, t):
        self.update_snap_time(t)  # snap function as promised

    def Background(self):
        self.qm.set_io1_value(7)

    def measure_temperature(self, N_snaps):
        self.qm.set_io_values(8, int(N_snaps))
# qm.set_io1_value(True)

if __name__ == "__main__":
    pgc_experiment = pgc(Config_exp.config)

# pgc_experiment.toggle_camera_roll(True)

# qmm = QuantumMachinesManager()
# qm = qmm.open_qm(Config_exp.Config_exp)