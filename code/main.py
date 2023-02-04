import os
import glob
import pickle
import pandas as pd
import numpy as np
from joblib import load
from auxiliary.paths import results_path,  input_path, model_path
from bmdn.bmdn_predict import FinalPredict, Process_Final
from tensorflow.keras.models import load_model
from auxiliary.correct_extinction import correction 
from auxiliary.columns import create_colors

if __name__ == "__main__":
    correct_ext = True
    model = {}
    aper = "PStotal"
    features = create_colors(broad=True, narrow=True, wise=True, galex=True, aper=aper)
    rf_path = os.path.join(model_path, "rf")

    if correct_ext:
        list_files = glob.glob(os.path.join(input_path, "*ext.csv"))
        bmdn_path = os.path.join(model_path, "bmdn", "ext")
        model["bmdn"] = load_model(os.path.join(bmdn_path, "SavedModels", "Fold0"), compile=False)
        Scaler_1 = load(os.path.join(bmdn_path, 'Scaler_1_Quantile.joblib'))
        Scaler_2 = load(os.path.join(bmdn_path, 'Scaler_2_MinMax.joblib'))
        model["rf"] = pickle.load(open(os.path.join(rf_path, "RF_final_extinction.sav"), 'rb'))
    else:
        list_files = glob.glob(os.path.join(input_path, "*VAC.csv"))
        bmdn_path = os.path.join(model_path, "bmdn", "ext")
        model["bmdn"] = load_model(os.path.join(bmdn_path, "SavedModels", "Fold0"), compile=False)
        Scaler_1 = load(os.path.join(bmdn_path, 'Scaler_1_Quantile.joblib'))
        Scaler_2 = load(os.path.join(bmdn_path, 'Scaler_2_MinMax.joblib'))
        model["rf"] = pickle.load(open(os.path.join(rf_path, "RF_final.sav"), 'rb'))


    HeaderToSave = ['ID', 'RA', 'DEC', 'zphot', 'zphot_2.5p', 'zphot_16p', 'zphot_84p', 'zphot_97.5p',
                            'pdf_peaks', 'zphot_second_peak', 'pdf_width', 'odds']
    for i in range(7):
        HeaderToSave.append(f'pdf_weight_{i}')
    for i in range(7):
        HeaderToSave.append(f'pdf_mean_{i}')
    for i in range(7):
        HeaderToSave.append(f'pdf_std_{i}')
    Header = HeaderToSave

    for file in list_files:
        chunk = pd.read_table(file, sep=",")
        # print(chunk)
        chunk = chunk.reset_index(drop=True)

        if correct_ext:
            chunk = correction(chunk)
        
        PredictSample, PredictFeatures, PredictMask = Process_Final(chunk, aper)
        print(features)
        print(PredictFeatures)
        PredictSample_Features = Scaler_2.transform(Scaler_1.transform(PredictSample[PredictFeatures]))
        PredictSample_Features[PredictMask] = 0

        Result_DF = FinalPredict(model["bmdn"], chunk[features], PredictSample_Features)

        # Saving results DataFrame
        Result_DF[HeaderToSave].to_csv(os.path.join(results_path, f'{file}.csv'), mode='a', index=False)

        z = model["rf"].predict(chunk[features])
        z.to_csv(os.path.join(results_path, f'{file}'+'_rf.csv'), mode='a', index=False)


    # PZ_Model = load_model(os.path.join(model, 'Fold0'), compile=False)

    # Files_to_predict_parallel = 2
    # Threads = np.arange(0, len(Files)+1, 1)

    # Processes = {}
    # for i in range(len(Threads)-1):
    #     Processes[i] = Thread(target=PredictForFileNoTry,
    #                             args=(Files[Threads[i]:Threads[i+1]], folders))

    # for lista in np.array_split(np.arange(0, len(Threads)-1), np.ceil(len(Threads)/Files_to_predict_parallel)):
    #     for i in lista:
    #         Processes[i].start()
    #         sleep(1.5)

    #     for i in lista:
    #         Processes[i].join()
