#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import logging
import time
from cycler import cycler
from matplotlib.colors import hsv_to_rgb
from utils import equal_gain, maximal_ratio, direct, selective, check_modes
from test_utils import load_mat

# ? Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # * Set logging level here (DEBUG or INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)-8s :: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# ? Configure plotting
plt.style.use('seaborn-darkgrid')
plt.rcParams['font.family'] = 'DeJavu Serif'
plt.rcParams['font.serif'] = ['Computer Modern']
plt.rcParams['figure.figsize'] = 13, 7

# ? For choosing function and in logs
method_dict = {"egc":("Equal Gain", equal_gain),"mrc":("Maximal Ratio", maximal_ratio), "dirc":("Direct",direct),"selc":("Selective",selective)}

def simulate_combining(sample_num, no_of_paths, snr_arange, fading, mode):

    start = time.time()

    SNR_dB_list = np.arange(*snr_arange)

    mode_n =  check_modes(mode)
    if not mode_n:
        logger.error(f"Error in mode: {mode}")
        return -1

    BER = np.zeros((len(SNR_dB_list),no_of_paths,len(mode_n)))
    
    for SNR_index, SNR_dB in enumerate(SNR_dB_list):
        SNR = 10 ** (SNR_dB / 10)

        data = np.random.rand(2, sample_num)
        qpsk_data2 = 2 * (data > 0.5).astype(int) -1
        
        L=-1
        qpsk_data = load_mat(L, SNR_index, name="d")
        E_signal = np.sqrt(2)
        E_noise = E_signal/ SNR 
        
        for L in range(1,no_of_paths+1):

            noise = load_mat(L, SNR_index, name="n")
            
           

            if fading.lower() == "rayleigh":
                gain = load_mat(L, SNR_index, name="g")
            elif fading.lower() == "rician":
                gain = np.random.normal(1/2, 1/2, size = (1,sample_num,L)) + \
                    ((0+1j)*np.random.normal(1/np.sqrt(2), 1/2 ,size = (1,sample_num,L)))
            else:
                logger.error(f"{fading} fading channel is not defined.")
                return -1
           
            gain_qpsk = np.tile(gain,[2,1,1])
           
            # transmitted_signal = np.tile(qpsk_data, [1,1,L])
            transmitted_signal = np.kron(np.ones((1,1,L)), qpsk_data[:,:,np.newaxis])
            # print(transmitted_signal[:10])
            # print(load_mat(L, SNR_index, name="t")[:10])

            print(np.count_nonzero(transmitted_signal!=load_mat(L, SNR_index, name="t")))
            received_signal = gain_qpsk * transmitted_signal + noise

            for BER_index, method in enumerate(mode_n):
                BER[SNR_index, L-1, BER_index] = method_dict[method][1](gain_qpsk, received_signal, sample_num, qpsk_data)
                logger.debug(f"BER = {BER[SNR_index, L-1, BER_index]:<10} For Mode :: {method_dict[method][0]:<15} SNR = {SNR_dB:<5} No of diversity branches = {L}")

    sim_time = time.time() - start
    logger.debug(f"Time taken: {sim_time}s")

    for ind, m in enumerate(mode_n):
        plt.plot(SNR_dB_list, BER[:,:,ind], ':o')
        plt.yscale("log")
        plt.xticks(SNR_dB_list)
        
        plt.legend([f"L={l}" for l in range(1,no_of_paths+1)])
        plt.figtext(.5,.9,f"{method_dict[m][0]} Combining - R{fading[1:]}", fontsize=20, ha='center')
        plt.xlabel("SNR (in dB)")
        plt.ylabel("BER")
        plt.show()
        # plt.savefig(f"./docs/{method_dict[m][0]} Combining - R{fading[1:]}.png")
        # plt.clf()
        

if __name__ =="__main__":

    SAMPLE_NUM = 10000
    NO_OF_PATHS = 4
    SNR_ARANGE = (1, 8, 2)
    FADING="rayleigh"
    MODE=("mrc",)

    simulate_combining(SAMPLE_NUM,NO_OF_PATHS,SNR_ARANGE,FADING,MODE)
    