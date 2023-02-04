import os
from pandas import read_csv
from tqdm import tqdm
from gc import collect
import numpy as np
from pandas import DataFrame
from tqdm import tqdm
from scipy import integrate
import tensorflow_probability as tfp; tfd = tfp.distributions
from auxiliary.paths import data_path
from auxiliary.metrics import Odds, Q
from auxiliary.columns import splus, wise, galex


def PredictForFileNoTry(files_list:list, folders:dict, aper='PStotal'):

    Progress_Bar = tqdm(files_list)
    for file in Progress_Bar:
        Progress_Bar.set_description(f'# Predicting for file: {file}')
        
        HeaderToSave = ['ID', 'RA', 'DEC', 'zphot', 'zphot_2.5p', 'zphot_16p', 'zphot_84p', 'zphot_97.5p',
                        'pdf_peaks', 'zphot_second_peak', 'pdf_width', 'odds']
        for i in range(7):
            HeaderToSave.append(f'pdf_weight_{i}')
        for i in range(7):
            HeaderToSave.append(f'pdf_mean_{i}')
        for i in range(7):
            HeaderToSave.append(f'pdf_std_{i}')
        Header = HeaderToSave

        Pred_in_chunks = False
        chunk = read_csv(os.path.join(folders['input'], f'{file}.csv'))
        ChunkSize = 50000
        if len(chunk) >= ChunkSize:
            Pred_in_chunks = True
            print(f'# File {file} is too large, predicting in chunks...')

        ### Processing data (calculate colours, ratios, mask) ###
        if Pred_in_chunks:
            for chunk in read_csv(os.path.join(folders['input'], f'{file}.csv'), chunksize=ChunkSize):

                try: 
                    chunk.rename(columns={'B_in': 'B'}, inplace=True)
                except:
                    pass

                chunk = chunk.reset_index(drop=True)
                # chunk = Correct_Extinction(chunk, aper)

                PredictSample, PredictFeatures, PredictMask = Process_Final(chunk, aper)
                PredictSample_Features = Scaler_2.transform(Scaler_1.transform(PredictSample[PredictFeatures]))
                PredictSample_Features[PredictMask] = 0

                Result_DF = FinalPredict(PZ_Model, chunk, PredictSample_Features)

                # Saving results DataFrame
                Result_DF[HeaderToSave].to_csv(os.path.join(folders['output'], f'{file}.csv'),
                                               mode='a', index=False, header=Header)
                Header = None
        
        else:

            chunk = chunk.reset_index(drop=True)
            # chunk = Correct_Extinction(chunk, aper)

            PredictSample, PredictFeatures, PredictMask = Process_Final(chunk, aper)
            PredictSample_Features = Scaler_2.transform(Scaler_1.transform(PredictSample[PredictFeatures]))
            PredictSample_Features[PredictMask] = 0

            Result_DF = FinalPredict(PZ_Model, chunk, PredictSample_Features)

            # Saving results DataFrame
            Result_DF[HeaderToSave].to_csv(os.path.join(folders['output'], f'{file}.csv'), mode='a', index=False)


def Process_Final(Dataframe, Aper:str):
    
    Errors_SPLUS = ['e_'+item for item in splus]
    Magnitudes = galex + splus + wise  # It's important to keep this order
    
    # Non detected/observed objects
    for feature in Magnitudes:
        Dataframe[feature][~Dataframe[feature].between(10, 50)] = np.nan

    # Replace S-PLUS missing features with the upper magnitude limit (the value in the error column)
    for feature, error in zip(splus, Errors_SPLUS):
        Dataframe[feature].fillna(Dataframe[error], inplace=True)
    
    # Calculate features (colors)    
    Reference_Mag  = 'r_'+Aper
    Reference_Idx = Magnitudes.index(Reference_Mag)
    MagnitudesToLeft = Magnitudes[:Reference_Idx]
    MagnitudesToRight = Magnitudes[(Reference_Idx+1):]

    for feature in MagnitudesToLeft: # of Reference_Mag
        Dataframe[feature+'-'+Reference_Mag] = Dataframe[feature] - Dataframe[Reference_Mag]

    for feature in MagnitudesToRight: # of Reference_Mag
        Dataframe[Reference_Mag+'-'+feature] = Dataframe[Reference_Mag] - Dataframe[feature]
    
    Training_Features = []
    for s in Dataframe.columns.values:
        if '-' in s:
            if s.split('-')[0] in Magnitudes and s.split('-')[1] in Magnitudes:
                Training_Features.append(s)
    
    # Mask
    Mask = Dataframe[Training_Features].isna().reset_index(drop=True)

    return Dataframe, Training_Features, Mask


def Calc_PDF(x, Weights, Means, STDs):
    PDF = np.sum( Weights * (1/(STDs*np.sqrt(2*np.pi))) * np.exp((-1/2)*((x[:, None]-Means)**2)/(STDs)**2), axis=1 )
    return PDF/np.trapz(PDF, x)


def FinalPredict(Model:dict, Testing_Dataframe, Testing_Data_Features, Num_Samples=200):
    
    x = np.linspace(0, 7, 7000, endpoint=True)
    
    Result_DF = DataFrame()
    Result_DF['ID'] = Testing_Dataframe['ID'].values
    Result_DF['RA'] = Testing_Dataframe['RA'].values
    Result_DF['DEC'] = Testing_Dataframe['DEC'].values
    
    Samples_Weights = []
    Samples_Means = []
    Samples_STDs = []
    for i in tqdm(range(Num_Samples)):
        
        Pred = Model(Testing_Data_Features)
        Weight = Pred.submodules[1].probs_parameter().numpy()
        Mean = Pred.submodules[0].mean().numpy().reshape(len(Testing_Data_Features), np.shape(Weight)[1])
        Std = Pred.submodules[0].stddev().numpy().reshape(len(Testing_Data_Features), np.shape(Weight)[1])
        
        Sorted_Weight_Index = np.flip(np.argsort(Weight, axis=1), axis=1)
        Samples_Weights.append(Weight[np.arange(len(Weight))[:,None], Sorted_Weight_Index])
        Samples_Means.append(Mean[np.arange(len(Mean))[:,None], Sorted_Weight_Index])
        Samples_STDs.append(Std[np.arange(len(Std))[:,None], Sorted_Weight_Index])

    Final_Weights = np.median(Samples_Weights, axis=0)
    Final_Means = np.median(Samples_Means, axis=0)
    Final_STDs = np.median(Samples_STDs, axis=0)
    
    del Samples_Weights
    del Samples_Means
    del Samples_STDs
    collect()

    PDF = tfd.MixtureSameFamily(mixture_distribution=tfd.Categorical(probs=Final_Weights),
          components_distribution=tfd.Normal(loc=Final_Means, scale=Final_STDs))
    PDF_STDs = PDF.stddev().numpy()

    Fine_ZPhot = []
    Final_PDFs = []
    Oddss = []
    Q68_Lower = []
    Q68_Higher = []
    Q95_Lower = []
    Q95_Higher = []
    for i in range(len(Testing_Data_Features)):
        
        Obj_PDF = Calc_PDF(x, Final_Weights[i], Final_Means[i], Final_STDs[i])
        Final_PDFs.append(Obj_PDF)
        Approx_Zphot = x[np.argmax(Obj_PDF)]
        x_detailed = np.linspace(Approx_Zphot-0.025, Approx_Zphot+0.025, 400)
        Fine_ZPhot.append(x_detailed[np.argmax(
            Calc_PDF(x_detailed, Final_Weights[i], Final_Means[i], Final_STDs[i])
            )])

        Obj_CDF = integrate.cumtrapz(Obj_PDF, x, initial=0)
        Oddss.append(Odds(x, Obj_CDF, Fine_ZPhot[i]))
        Q68_Lower.append(Q(68, x, Obj_CDF))
        Q68_Higher.append(Q(68, x, Obj_CDF, lower=False))
        Q95_Lower.append(Q(95, x, Obj_CDF))
        Q95_Higher.append(Q(95, x, Obj_CDF, lower=False))
        
    Sec_ZPhot = []
    Num_Peaks = []
    for i in range(len(Final_PDFs)):
        Diff = np.diff(Final_PDFs[i])/np.diff(x)
        Peak_Idx = np.where(np.diff(np.sign(Diff)) == -2)[0]

        if np.sum(Final_PDFs[i][Peak_Idx] >= np.max(Final_PDFs[i])/3) >= 2:

            Num_Peaks.append(np.sum(Final_PDFs[i][Peak_Idx] >= np.max(Final_PDFs[i])/3))
            Sorted_Idxs = Peak_Idx[np.argsort(Final_PDFs[i][Peak_Idx])[::-1]]

            if np.count_nonzero(Final_PDFs[i][Peak_Idx] >= np.max(Final_PDFs[i])/3) >= 2:
                Sorted_Idxs = Sorted_Idxs[:2]
                Sec_ZPhot.append(x[Sorted_Idxs[-1]])

        else:
            Num_Peaks.append(1)
            Sec_ZPhot.append(np.nan)

    Result_DF['zphot'] = Fine_ZPhot
    Result_DF['zphot_2.5p'] = Q95_Lower
    Result_DF['zphot_16p'] = Q68_Lower
    Result_DF['zphot_84p'] = Q68_Higher
    Result_DF['zphot_97.5p'] = Q95_Higher
    Result_DF['pdf_peaks'] = Num_Peaks
    Result_DF['zphot_second_peak'] = Sec_ZPhot
    Result_DF['pdf_width'] = PDF_STDs
    Result_DF['odds'] = Oddss
        
    for i in range(len(Final_Weights[0])):
        Result_DF[f'pdf_weight_{i}'] = np.round(Final_Weights[:,i], 8)
    for i in range(len(Final_Means[0])):
        Result_DF[f'pdf_mean_{i}'] = np.round(Final_Means[:,i], 8)
    for i in range(len(Final_STDs[0])):
        Result_DF[f'pdf_std_{i}'] = np.round(Final_STDs[:,i], 8)
        
    Result_DF.fillna(-99, inplace=True)
    Result_DF = Result_DF.astype({'ID': str, 'RA': np.float64, 'DEC': np.float64, 'zphot': np.float32,
                                  'zphot_2.5p': np.float32, 'zphot_16p': np.float32,
                                  'zphot_84p': np.float32, 'zphot_97.5p': np.float32,
                                  'pdf_peaks': np.float32, 'zphot_second_peak': np.float32,
                                  'pdf_width': np.float32, 'odds': np.float32})

    return Result_DF
