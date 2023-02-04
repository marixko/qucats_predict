import pandas as pd
import sfdmap
import extinction
from auxiliary.paths import data_path
import numpy as np
from auxiliary.columns import splus, wise, galex
def correction(data):
    chunk = data.copy(deep=True)

    feat = galex+splus+wise
    m = sfdmap.SFDMap('/Volumes/GoogleDrive/My Drive/Research/Projects/qucats_predict/data/dustmaps')
    EBV = m.ebv(chunk.RA, chunk.DEC)

    # Obtendo A_v nesta mesma posição
    AV  = m.ebv(chunk.RA, chunk.DEC)*3.1

    # Calculando a extinção em outros comprimentos de onda
    # Utilizando a lei de extinção de Cardelli, Clayton & Mathis.
    Lambdas = np.array([1549.02, 2304.74,                                                        # FUV, NUV
                        3536, 3770, 3940, 4094, 4292, 4751, 5133, 6258, 6614, 7690, 8611, 8831,  
                        33526.00, 46028.00])

    Extinctions = []
    for i in range(len(AV)):
        Extinctions.append(extinction.ccm89(Lambdas, AV[i], 3.1))

    Extinction_DF = pd.DataFrame(Extinctions, columns=feat)
    chunk = chunk.reset_index(drop=True)

    mask_99 = chunk[feat]==99
    chunk[feat] = chunk[feat].sub(Extinction_DF)
    chunk[feat] = chunk[feat].mask(mask_99, other = 99)
    return chunk

