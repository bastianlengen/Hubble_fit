###  Fit functions
import numpy as np
import pandas as pd
from Values import *

# Fit H0
def find_H0(Cepheids: pd.DataFrame, SN: pd.DataFrame , galaxies: list, display_text: bool =False):  ### Moertsell 2021
    ### Create y vector
    MW_filter = Cepheids['Gal'] == 'MW'
    y = np.array(Cepheids[MW_filter]['m_W'] - 10 + 5 * np.log10(Cepheids[MW_filter]['pi']))
    y = np.append(y, Cepheids[~MW_filter]['m_W'])
    y = np.append(y, [mu_N4258, mu_LMC])
    y = np.append(y, SN['m_b'])

    ### Create the parameters vector
    # 0-18 : mu_host // 19-20 : mu_N4258, mu_LMC // 21 : mW
    #  22-23 : bs, bl // 24-25 : ZW, zp // 26 : MB
    q = np.zeros(27)

    ### Create vector P and [O/H] in the good galaxy order
    logP = np.append(Cepheids[MW_filter]['logP'], Cepheids[~MW_filter]['logP'])
    MH = np.append(Cepheids[MW_filter]['M/H'], Cepheids[~MW_filter]['M/H'])

    ### Create the Design matrix :
    L = np.zeros((len(y), len(q)))
    Cepheids_count = 0
    SN_count = 0
    for i in range(0, len(y)):
        if i < len(Cepheids[MW_filter]):
            MW_index_offset = len(Cepheids[~MW_filter])  #  since MW are last in DF and here first.
            L[i][21] = 1  #  mW
            if logP[i] < 1:
                L[i][22] = logP[i] - 1
            else:
                L[i][23] = logP[i] - 1
            L[i][24] = MH[i]
            L[i][25] = -5 / np.log(10) / Cepheids['pi'][MW_index_offset + i]
        elif i < len(Cepheids):
            galaxy_index = np.where(galaxies == Cepheids['Gal'][Cepheids_count])[0][0]  #  Index restart at 0
            Cepheids_count = Cepheids_count + 1
            L[i][galaxy_index] = 1  # mu0
            L[i][21] = 1  #  mW
            if logP[i] < 1:
                L[i][22] = logP[i] - 1
            else:
                L[i][23] = logP[i] - 1
            L[i][24] = MH[i]
        elif i < len(Cepheids) + 1:
            L[i][19] = 1
        elif i < len(Cepheids) + 2:
            L[i][20] = 1
        else:
            L[i][SN_count] = 1
            SN_count = SN_count + 1
            L[i][26] = 1

    ### Create the correlation matrix :
    sigma2_pi = Cepheids[MW_filter]['sig_m_W'] ** 2 \
                + (5 / np.log(10) / Cepheids[MW_filter]['pi'] * Cepheids[MW_filter]['sig_pi']) ** 2
    diag_sigma = np.array(sigma2_pi)  # for MW
    diag_sigma = np.append(diag_sigma,
                           Cepheids[~MW_filter]['sig_m_W'] ** 2 + added_scatter ** 2)  # for host, N4258 & LMC
    diag_sigma = np.append(diag_sigma, [sigma_N4258 ** 2, sigma_LMC ** 2])  # geometric distances
    diag_sigma = np.append(diag_sigma, SN['sig'] ** 2)
    C = np.diag(diag_sigma)

    ### Find the optimal parameters :
    LT = np.transpose(L)
    C1 = np.linalg.inv(C)
    cov = np.linalg.inv(np.matmul(np.matmul(LT, C1), L))
    q = np.matmul(np.matmul(np.matmul(cov, LT), C1), y)
    chi2 = np.matmul(np.matmul(np.transpose(y - np.matmul(L, q)), C1), y - np.matmul(L, q))

    mu_hat_N4258, mu_hat_LMC, m_w_H, b_s, b_l, Z_W, zp, M_B = q[19], q[20], q[21], q[22], q[23], q[24], q[25], q[26]
    logH_0 = ((M_B + 5 * a_b + 25) / 5)
    H_0 = 10 ** logH_0
    sigma_M_B = np.sqrt(cov[26][26])
    sigma_logH0 = np.sqrt((0.2 * sigma_M_B) ** 2 + sigma_a_b ** 2)
    sigma_H_0 = np.log(10) * H_0 * sigma_logH0
    sigma_mu_hat_N4258, sigma_mu_hat_LMC = np.sqrt(cov[19][19]), np.sqrt(cov[20][20])
    sigma_m_w_H, sigma_b_s, sigma_b_l = np.sqrt(cov[21][21]), np.sqrt(cov[22][22]), np.sqrt(cov[23][23])
    sigma_Z_W, sigma_zp = np.sqrt(cov[24][24]), np.sqrt(cov[25][25])

    if display_text == True :
        print('mu_hat_N4258 = %f +/- %f' % (mu_hat_N4258, sigma_mu_hat_N4258))
        print('mu_hat_LMC = %f +/- %f' % (mu_hat_LMC, sigma_mu_hat_LMC))
        print('m_w_H = %f +/- %f' % (m_w_H, sigma_m_w_H))
        print('b_s = %f +/- %f' % (b_s, sigma_b_s))
        print('b_l = %f +/- %f' % (b_l, sigma_b_l))
        print('Z_W = %f +/- %f' % (Z_W, sigma_Z_W))
        print('zp = %f +/- %f' % (zp, sigma_zp))
        print('M_B = %f +/- %f' % (M_B, sigma_M_B))
        print('a_b = %f +/- %f' % (a_b, sigma_a_b))
        print('H_0 = %f +/- %f' % (H_0, sigma_H_0))
        print('chi2 = %f' % chi2)
        print('chi2/dof = %f' % (chi2 / len(y)))

    return q, H_0, chi2, cov, y, L, sigma_H_0