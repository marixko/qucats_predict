import os
import pandas as pd
import sfdmap
import extinction
from auxiliary.paths import data_path
import numpy as np
from auxiliary.columns import splus, wise, galex

def correction(data, feat=[]):
    chunk = data.copy(deep=True)

    if not feat:
        feat = galex + splus + wise

    m = sfdmap.SFDMap(os.path.join(data_path, 'dustmaps'))
    EBV = m.ebv(chunk.RA, chunk.DEC)

    # Obtendo A_v nesta mesma posição
    AV  = m.ebv(chunk.RA, chunk.DEC)*3.1

    # Calculando a extinção em outros comprimentos de onda
    # Utilizando a lei de extinção de Cardelli, Clayton & Mathis.
    
    lambdas_dict = {'FUVmag': 1549.02, 'NUVmag': 2304.74,
                    'u_PStotal': 3536, 'J0378_PStotal': 3770, 'J0395_PStotal': 3940, 'J0410_PStotal': 4094,
                    'J0430_PStotal': 4292, 'g_PStotal': 4751, 'J0515_PStotal': 5133, 'r_PStotal': 6258,
                    'J0660_PStotal': 6614, 'i_PStotal': 7690, 'J0861_PStotal': 8611, 'z_PStotal': 8831,
                    'W1': 33526, 'W2': 46028}
    
    lambdas = []
    for mag in feat:
        lambdas.append(lambdas_dict[mag])
    lambdas = np.array(lambdas, dtype=float)

    Extinctions = []
    for i in range(len(AV)):
        Extinctions.append(extinction.ccm89(lambdas, AV[i], 3.1))

    Extinction_DF = pd.DataFrame(Extinctions, columns=feat)
    chunk = chunk.reset_index(drop=True)

    mask_99 = chunk[feat]==99
    chunk[feat] = chunk[feat].sub(Extinction_DF)
    chunk[feat] = chunk[feat].mask(mask_99, other=99)
    chunk.index = data.index
    return chunk



