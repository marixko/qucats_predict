import os
import gc
import logging
import warnings

import numpy as np
from pandas import DataFrame, read_csv
from tqdm import tqdm
import joblib
#from scipy.integrate import cumtrapz
from tensorflow.keras.models import load_model
import tensorflow_probability as tfp; tfd = tfp.distributions

# from auxiliary.metrics import Odds, Q
from auxiliary.columns import calculate_colors, aper, splus, broad, narrow, wise, galex, error_splus


warnings.filterwarnings('ignore')
logging.getLogger('tensorflow').setLevel(logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def preprocess_BMDN(dataframe, feature_list:list, Scaler_1, Scaler_2):
    
    # Replace S-PLUS missing features with the upper magnitude limit (the value in the error column)
    for mag, error in zip(splus, error_splus):
        dataframe.loc[dataframe[mag]==99, mag] = dataframe.loc[dataframe[mag]==99, error]

    # Identify which groups of magnitudes are present in feature_list colors in order to calculate colors
    colors = [feat for feat in feature_list if ('-' in feat)]
    check_pair = lambda x: x[0] if x[1]==f'r_{aper}' else x[1]
    mag_list = [check_pair(feat.split('-')) for feat in colors]
    
    broad_bool = broad[0] in mag_list
    narrow_bool = narrow[0] in mag_list
    wise_bool = wise[0] in mag_list
    galex_bool = galex[0] in mag_list
    dataframe = calculate_colors(dataframe, broad_bool, narrow_bool, wise_bool, galex_bool)
    
    # Scaling features
    features = Scaler_2.transform(Scaler_1.transform(dataframe[feature_list]))
    
    # Masking missing bands
    mask = dataframe[feature_list].isna().reset_index(drop=True)
    features[mask] = 0

    return dataframe, features


def Calc_PDF(x, Weights, Means, STDs):
    '''To calculate PDFs.'''
    if isinstance(Weights, str):
        Weights = np.fromstring(Weights, sep=',')
        Means = np.fromstring(Means, sep=',')
        STDs = np.fromstring(STDs, sep=',')
    PDF = np.sum( Weights * (1/(STDs*np.sqrt(2*np.pi))) * np.exp((-1/2)*((x[:, None]-Means)**2)/(STDs)**2), axis=1 )
    return PDF/np.trapz(PDF, x)


def FinalPredict(Model, Dataframe, Data_Features, Num_Samples=200):
    
    x = np.linspace(0, 5, 5000, endpoint=True)
    
    Result_DF = DataFrame()
    Result_DF['ID'] = Dataframe['ID'].values
    Result_DF['RA'] = Dataframe['RA'].values
    Result_DF['DEC'] = Dataframe['DEC'].values
    
    Samples_Weights = []
    Samples_Means = []
    Samples_STDs = []
    for i in tqdm(range(Num_Samples)):
        Pred = Model(Data_Features)
        Weight = Pred.submodules[1].probs_parameter().numpy()
        Mean = Pred.submodules[0].mean().numpy().reshape(len(Data_Features), np.shape(Weight)[1])
        Std = Pred.submodules[0].stddev().numpy().reshape(len(Data_Features), np.shape(Weight)[1])
        
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
    gc.collect()

    # PDF = tfd.MixtureSameFamily(mixture_distribution=tfd.Categorical(probs=Final_Weights),
    #       components_distribution=tfd.Normal(loc=Final_Means, scale=Final_STDs))
    # PDF_STDs = PDF.stddev().numpy()

    Fine_ZPhot = []
    Final_PDFs = []
    # Oddss = []
    # Q68_Lower = []
    # Q68_Higher = []
    # Q95_Lower = []
    # Q95_Higher = []
    for i in range(len(Data_Features)):
        
        Obj_PDF = Calc_PDF(x, Final_Weights[i], Final_Means[i], Final_STDs[i])
        Final_PDFs.append(Obj_PDF)
        Approx_Zphot = x[np.argmax(Obj_PDF)]
        x_detailed = np.linspace(Approx_Zphot-0.025, Approx_Zphot+0.025, 400)
        Fine_ZPhot.append(x_detailed[np.argmax(
            Calc_PDF(x_detailed, Final_Weights[i], Final_Means[i], Final_STDs[i])
            )])

        # Obj_CDF = cumtrapz(Obj_PDF, x, initial=0)
        # Oddss.append(Odds(x, Obj_CDF, Fine_ZPhot[i]))
        # Q68_Lower.append(Q(68, x, Obj_CDF))
        # Q68_Higher.append(Q(68, x, Obj_CDF, lower=False))
        # Q95_Lower.append(Q(95, x, Obj_CDF))
        # Q95_Higher.append(Q(95, x, Obj_CDF, lower=False))
        
    # Sec_ZPhot = []
    Num_Peaks = []
    for i in range(len(Final_PDFs)):
        Diff = np.diff(Final_PDFs[i])/np.diff(x)
        Peak_Idx = np.where(np.diff(np.sign(Diff)) == -2)[0]

        if np.sum(Final_PDFs[i][Peak_Idx] >= np.max(Final_PDFs[i])/3) >= 2:

            Num_Peaks.append(np.sum(Final_PDFs[i][Peak_Idx] >= np.max(Final_PDFs[i])/3))
            Sorted_Idxs = Peak_Idx[np.argsort(Final_PDFs[i][Peak_Idx])[::-1]]

            if np.count_nonzero(Final_PDFs[i][Peak_Idx] >= np.max(Final_PDFs[i])/3) >= 2:
                Sorted_Idxs = Sorted_Idxs[:2]
                # Sec_ZPhot.append(x[Sorted_Idxs[-1]])

        else:
            Num_Peaks.append(1)
            # Sec_ZPhot.append(np.nan)

    Result_DF['z_bmdn_peak'] = Fine_ZPhot
    # Result_DF['zphot_2.5p'] = Q95_Lower
    # Result_DF['zphot_16p'] = Q68_Lower
    # Result_DF['zphot_84p'] = Q68_Higher
    # Result_DF['zphot_97.5p'] = Q95_Higher
    Result_DF['n_peaks_bmdn'] = Num_Peaks
    # Result_DF['zphot_second_peak'] = Sec_ZPhot
    # Result_DF['pdf_width'] = PDF_STDs
    # Result_DF['odds'] = Oddss
        
    for i in range(len(Final_Weights[0])):
        Result_DF[f'z_bmdn_pdf_weight_{i+1}'] = np.round(Final_Weights[:,i], 8)
    for i in range(len(Final_Means[0])):
        Result_DF[f'z_bmdn_pdf_mean_{i+1}'] = np.round(Final_Means[:,i], 8)
    for i in range(len(Final_STDs[0])):
        Result_DF[f'z_bmdn_pdf_std_{i+1}'] = np.round(Final_STDs[:,i], 8)
        
    Result_DF = Result_DF.astype({
        'ID': str, 'RA': np.float64, 'DEC': np.float64,
        'z_bmdn_peak': np.float32,
        # 'zphot_2.5p': np.float32,
        # 'zphot_16p': np.float32,
        # 'zphot_84p': np.float32,
        # 'zphot_97.5p': np.float32,
        'n_peaks_bmdn': np.float32,
        # 'zphot_second_peak': np.float32,
        # 'pdf_width': np.float32,
        # 'odds': np.float32
        })

    return Result_DF


def PredictForFileNoTry(files_list:list, folders:dict):
    
    # Loading the model
    model = os.path.join(folders['model'], 'SavedModels')
    PZ_Model = load_model(os.path.join(model, 'Fold0'), compile=False)

    # Loading scalers
    Scaler_1 = joblib.load(os.path.join(folders['model'], 'Scaler_1_Quantile.joblib'))
    Scaler_2 = joblib.load(os.path.join(folders['model'], 'Scaler_2_MinMax.joblib'))
    
    # Loading features
    with open(os.path.join(folders['model'], 'Model_Summary.txt'), 'r') as summary_file:
        feature_list = eval(summary_file.readlines()[-1])

    Progress_Bar = tqdm(files_list)
    for file in Progress_Bar:
        Progress_Bar.set_description(f'# Predicting for file: {file}')
        
        HeaderToSave = ['ID', 'RA', 'DEC', 'z_bmdn_peak', 'n_peaks_bmdn']
        for i in range(1, 8):
            HeaderToSave.append(f'z_bmdn_pdf_weight_{i}')
            HeaderToSave.append(f'z_bmdn_pdf_mean_{i}')
            HeaderToSave.append(f'z_bmdn_pdf_std_{i}')

        Pred_in_chunks = False
        chunk = read_csv(os.path.join(folders['input'], f'{file}.csv'))
        ChunkSize = 50000
        if len(chunk) >= ChunkSize:
            Pred_in_chunks = True
            print(f'# File {file} is too large, predicting in chunks...')

        ### Processing data (calculate colours, ratios, mask) ###
        if Pred_in_chunks:
            for chunk in read_csv(os.path.join(folders['input'], f'{file}.csv'), chunksize=ChunkSize):
                chunk = chunk.reset_index(drop=True)

                PredictSample, PredictSample_Features = preprocess_BMDN(chunk, feature_list, Scaler_1, Scaler_2)
                Result_DF = FinalPredict(PZ_Model, PredictSample, PredictSample_Features)

                # Saving results DataFrame
                Result_DF[HeaderToSave].to_csv(os.path.join(folders['output'], f'{file}.csv'),
                                               mode='a', index=False)
        
        else:
            chunk = chunk.reset_index(drop=True)

            PredictSample, PredictSample_Features = preprocess_BMDN(chunk, feature_list, Scaler_1, Scaler_2)
            Result_DF = FinalPredict(PZ_Model, PredictSample, PredictSample_Features)

            # Saving results DataFrame
            Result_DF[HeaderToSave].to_csv(os.path.join(folders['output'], f'{file}.csv'), mode='a', index=False)
