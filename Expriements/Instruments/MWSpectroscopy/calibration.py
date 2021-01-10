# Imports
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
import numpy as np
import qcodes.instrument_drivers.signal_hound.USB_SA124B
from scipy.optimize import fmin, brute
from sys import exit
import json
import datetime
import MWSpectroscopy.configurations as configurations


def optimize(config_args_path=None):
    """
    This function optimizes the DC offsets of the quantum controller to minimize the leakage at 7GHz
    :return: Prints the ideal values of the DC offsets and correction matrix variables
    """


    # The configuration of the quantum program
    if config_args_path is None:
        config_args = configurations.default_config_args()
    else:
        with open(config_args_path, 'r') as fp:
            config_args = json.load(fp)

    config = configurations.create_config(**config_args)
    # Initial guess for the best offsets
    # Initial guess for correction variables corvars = [0, 1]
    lo_freq = config_args['lo_frequency']
    im_freq = config_args['im_frequency']
    # Searching parameters, range of parameters for brute force, num of step in the brute force and max iteration fmin
    # OFFSETS
    nstepbruteoffset  = 10                         # Num of steps in the initial brute force stage(N^2)
    rangebruteoffset  = [(-0.1, 0.1), (-0.1, 0.1)]  # Range to look in the inital brute force stage
    maxiterfminoffset = 100                        # maximum number of iteration in the fmin stage

    # CORRECTION VARIABLES
    nstepbrutecorvars = 20                        # Num of steps in the initial brute force stage(N^2)
    rangebrutecorvars = [(-0.2, 0.2), (0.8, 1.2)]  # Range to look in the inital brute force stage
    maxiterfmincorvars = 100                      # maximum number of iteration in the fmin stage

    # OLD to initialize the spectrum analyzer
    try:
        # Initializes the instrument
        span = lo_freq/1000
        inst = setinstrument(lo_freq, span)

    except Exception as e:
        print("An error has occurred trying to initialize the instrument.\nThe Error:\n", e)
        exit()

    # The program that will run on the quantum machine
    with program() as prog:
        with infinite_loop_():
            play('pulse1', 'antena1')

    # Connects to the quantum machine through the network
    qmManager = QuantumMachinesManager()
    # Open quantum machine from configuration and force execute it
    qm1 = qmManager.open_qm(config)
    job = qm1.execute(prog, forceExecution=True)

    # array for saving values for graphs
    offsets_log = [[0, 0, 0]]
    corrections_log = [[0, 0, 0]]

    offsets = brute(power, rangebruteoffset, args=(qm1, inst, 'offset', im_freq,lo_freq, offsets_log),
                    Ns=nstepbruteoffset, finish=None)
    try:
        print('\n    Initial guess for the offsets [DC_I, DC_Q]: ', offsets, "\n\n")
        # Using fmin function to find the best offsets to minimize the leakage
        xopt = fmin(power, offsets, (qm1, inst, 'offset', im_freq, lo_freq, offsets_log),
                     maxiter=maxiterfminoffset)

    # If there's an error trying to use the "power" function
    except Exception as e:
        print("An error has occurred in the 'power' function. \nThe Error:\n", e)
        inst.close()  # Closes the spectrum analyzer

    # Redefine the offsets to the values we found
    offsets = xopt
    print("\nOptimal offsets [DC_I, DC_Q]: " + str(offsets) + "\n\n")

    # Define the spectrum analyzer frequency to the left spike frequency
    inst.frequency(lo_freq - im_freq)
    corvars = brute(power, rangebrutecorvars, args=(qm1, inst, 'correction', im_freq, lo_freq, corrections_log),
                    Ns=nstepbrutecorvars, finish=None)
    correction = configurations.calc_cmat(corvars)
    print(
        "\n    Initial guess from brute force [th, k]: " + str(corvars) + "\n\n")

    xopt = fmin(power, corvars, (qm1, inst, 'correction', im_freq, lo_freq, corrections_log),
                 maxiter=maxiterfmincorvars)

    corvars = xopt
    print("\nOptimal correction variables [theta, k]: " + str(corvars))

    final_string = """
    ---------------------------------------------------------------------------
    {}
    Final reslults:
        * Offsets [DC_I, DC_Q]: {}
        * Correction variables: {}
    ---------------------------------------------------------------------------
    \n""".format(datetime.date.today().strftime('%d\\%m\\%Y   %H:%M'), offsets, corvars)
    print(final_string)
    inst.close()  # Closesut the instrument

    with open('calibration_results.txt', 'a+') as results:
        results.write(final_string)

    np.savetxt('offsets_log.csv', np.array(offsets_log, dtype='float'), delimiter=',')
    np.savetxt('correction_log.csv', np.array(corrections_log, dtype='float'), delimiter=',')
    config_args['offsets']['I'] = offsets[0]
    config_args['offsets']['Q'] = offsets[1]
    config_args['correction_vars']['theta'] = corvars[0]
    config_args['correction_vars']['k'] = corvars[1]

    with open('conf_args.json', 'w+') as args_file:
        json.dump(config_args, args_file, indent=4, separators=(',', ': '))


def power(parameters, qm, inst, searchfor, im_freq, lo_freq, log_array):
    """
    This functions returns the amplitude on a specific frequency given offsets
    :param parameters: parametrs for sweep, DC offsets or correction variables
    :param qm: Quantum Manager of the program
    :param inst: The signal hound usb-SA124B
    :param searchfor: String that tells the function what is being optimized, 'offset' or 'correction'
    :param im_freq: intermediate frequency
    :param lo_freq: local oscillator frequency
    :param log_array: array to log parameters

    :return: The power of the frequency at the instrument's center frequency
    """

    # The "heart" of the function, sends the quantum machine a command to change the offsets and corrections
    if searchfor == 'offset':
        # DC offsets to separate variables
        DC_I = parameters[0]
        DC_Q = parameters[1]
        qm.set_output_dc_offset_by_element('antena1', 'I', float(DC_I))
        qm.set_output_dc_offset_by_element('antena1', 'Q', float(DC_Q))
        # Read the power of the leakage frequency, this is what we want to minimize
        power_leakge = inst.get('power')
        newrow = [DC_I, DC_Q, power_leakge]
        log_array.append(newrow)
        # Prints the result of each iteration
        print("Offsets [DC_I, DC_Q]: {}  => {:.2f}".format(parameters, power_leakge))
    elif searchfor == 'correction':
        # Set correction matrix
        th = parameters[0]
        k = parameters[1]
        correction_mat = configurations.calc_cmat([th, k])
        qm.set_mixer_correction('my_mixer', int(im_freq), int(lo_freq), correction_mat)
        # Read the power of the leakage frequency, this is what we want to minimize
        power_leakge = inst.get('power')
        newrow = [th, k, power_leakge]
        log_array.append(newrow)
        # Prints the result of each iteration
        print("Correction variables [theta, k]: {} => {:.2f}".format(parameters, power_leakge))
    else:
        raise KeyError('power function correction\\parameters type is not clear')

    return power_leakge  # Return the power of the leakage frequency


def setinstrument(freq, span):
    """
    Sets up the USB-SA 124B Signal Hound spectrum analyzer and returns it as a qCoDeS instrument object
    :param freq: Center frequency of the instrument
    :param span: the span of the frequency scan
    :return: The instrument as a QCoDeS instrument
    """
    # Sets instrument drivers and connections
    path = 'C:\\Program Files\\Signal Hound\\Spike\\sa_api.dll'  # device's driver location
    mysa = qcodes.instrument_drivers.signal_hound.USB_SA124B.SignalHound_USB_SA124B(
        'mysa', dll_path=path)

    print("\n"+"-"*80)
    print(mysa.get_idn())  # Prints instrument's details
    print("-"*80+"\n")

    mysa.frequency(freq)  # Center of scanned region
    mysa.span(span)  # Width of scan region
    mysa.configure()

    return mysa


if __name__ == '__main__':
    optimize()
