import pandas as pd
import sfdmap
import extinction
from .paths import data_path

def correction(data):
    chunk = data.copy(deep=True)

    Base_Filters   = ['u', 'J0378', 'J0395', 'J0410', 'J0430', 'g', 'J0515', 'r', 'J0660', 'i', 'J0861', 'z']
    Features_SPLUS = [filt+'_'+'PStotal' for filt in Base_Filters]
    m = sfdmap.SFDMap(data_path+'/dustmaps/')
    EBV = m.ebv(chunk.RA, chunk.DEC)

    # Obtendo A_v nesta mesma posição
    AV  = m.ebv(chunk.RA, chunk.DEC)*3.1

    # Calculando a extinção em outros comprimentos de onda
    # Utilizando a lei de extinção de Cardelli, Clayton & Mathis.
    Lambdas = np.array([3536., 3770., 3940., 4094., 4292., 4751., 5133., 6258., 6614., 7690., 8611., 8831.])

    Extinctions = []
    for i in range(len(AV)):
        Extinctions.append(extinction.ccm89(Lambdas, AV[i], 3.1))

    Extinction_DF = pd.DataFrame(Extinctions, columns=Features_SPLUS)
    chunk = chunk.reset_index(drop=True)

    mask_99 = chunk[Features_SPLUS]==99
    chunk[Features_SPLUS] = chunk[Features_SPLUS].sub(Extinction_DF)
    chunk[Features_SPLUS] = chunk[Features_SPLUS].mask(mask_99, other = 99)
    return chunk

