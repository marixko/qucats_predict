import os
os.environ['TF_XLA_FLAGS'] = '--tf_xla_enable_xla_devices'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import glob
from tqdm import tqdm
import pickle
import logging
import pandas as pd
from timeit import default_timer as timer
from datetime import timedelta
from joblib import load
from auxiliary.paths import results_path, model_path, predict_path, logs_path, save_corrected_path
from predict.bmdn import FinalPredict, Process_Final
from tensorflow.keras.models import load_model
from auxiliary.columns import create_colors


logging.basicConfig(filename=os.path.join(logs_path,'get_predictions.log'), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG, filemode='a')


def get_predictions(list_files, bmdn = True, rf = True, flex = True, correct_ext_model = True, replace=False, verbose=True):
    start_time = timer()
    logging.info("Using model trained with extinction-corrected data: %s" % correct_ext_model)

    if verbose:
        print("Starting predictions for %s files" % len(list_files) )
        print("Warning: if the result files already exists, they will be replaced by default for now! ")
        
    model = {}
    aper = "PStotal"
    features = create_colors(broad=True, narrow=True, wise=True, galex=True, aper=aper)

    try:
        if bmdn:
            if correct_ext_model:
                bmdn_path = os.path.join(model_path, "bmdn", "ext")
                model["bmdn"] = load_model(os.path.join(bmdn_path, "SavedModels", "Fold0"), compile=False)
                Scaler_1 = load(os.path.join(bmdn_path, 'Scaler_1_Quantile.joblib'))
                Scaler_2 = load(os.path.join(bmdn_path, 'Scaler_2_MinMax.joblib'))
            else:
                bmdn_path = os.path.join(model_path, "bmdn", "no_ext")
                model["bmdn"] = load_model(os.path.join(bmdn_path, "SavedModels", "Fold0"), compile=False)
                Scaler_1 = load(os.path.join(bmdn_path, 'Scaler_1_Quantile.joblib'))
                Scaler_2 = load(os.path.join(bmdn_path, 'Scaler_2_MinMax.joblib'))
    except Exception as e:
        print(e)
        logging.error(e)
        pass
    
    HeaderToSave = ['ID', 'RA', 'DEC', 'z_bmdn_peak', 'n_peaks_bmdn']

    for i in range(7):
        HeaderToSave.append(f'z_bmdn_pdf_weight_{i}')
    for i in range(7):
        HeaderToSave.append(f'z_bmdn_pdf_mean_{i}')
    for i in range(7):
        HeaderToSave.append(f'z_bmdn_pdf_std_{i}')

    try:
        if rf:
            rf_path = os.path.join(model_path, "rf")
            if correct_ext_model:
                model["rf"] = pickle.load(open(os.path.join(rf_path, "RF_final_extinction.sav"), 'rb'))
            else:
                model["rf"] = pickle.load(open(os.path.join(rf_path, "RF_final.sav"), 'rb'))
    except Exception as e: 
        print(e)
        logging.error(e)
        pass

    if rf == True or bmdn == True: 
        for file in tqdm(list_files):
            save_filename = file.split(os.path.sep)[-1].split('.')[0]
            logging.info("Starting for FIELD: %s" % save_filename)
            print("Starting for field: %s" % save_filename)
            table = pd.read_table(file, sep=",")
            table = table.reset_index(drop=True)
            
            try:
                if bmdn:
                    if verbose:
                        print("Calculating BMDN predictions...")
                    logging.info("Starting BMDN prediction")
                    chunk_bmdn = table.copy(deep=True)
                    PredictSample, PredictFeatures, PredictMask = Process_Final(chunk_bmdn, aper)
                    PredictSample_Features = Scaler_2.transform(Scaler_1.transform(PredictSample[PredictFeatures]))
                    PredictSample_Features[PredictMask] = 0

                    Result_DF = FinalPredict(model["bmdn"], chunk_bmdn, PredictSample_Features)

                    #Saving results DataFrame
                    Result_DF[HeaderToSave].to_csv(os.path.join(results_path, save_filename+"_bmdn.csv"), mode='a', index=False)
            except Exception as e:
                print(e)
                logging.error(e)
                pass

            try:
                if rf:
                    if verbose:
                        print("Calculating RF predictions...")
                    logging.info("Starting RF prediction")
                    z = model["rf"].predict(table[features])
                    table["z_rf"] = z
                    table[["ID",  "RA",  "DEC", "z_rf"]].to_csv(os.path.join(results_path, save_filename+"_rf.csv"), mode='a', index=False)
            except Exception as e:
                print(e)
                logging.error(e)
                pass

    try:
        if flex:
            if verbose:
                print("Calculating FlexCoDE predictions...")
            flex_path = os.path.join(predict_path, "flexcode.r")
            os.system(f"""Rscript {flex_path}""")
    except Exception as e:
        print(e)
        logging.error(e)
        pass
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
    end_time = timer()

    if verbose:
        print("Finished process. Total elapsed time: %s" % timedelta(seconds=end_time-start_time))
    logging.info("Finished process in %s" % timedelta(seconds=end_time-start_time))
    
    return
    
if __name__ == "__main__":
    logging.info("get_predictions.py was called.")
    replace = False
    correct_ext_model = True
    bmdn= True
    rf =  False
    flex = False
    
    list_files = glob.glob(os.path.join(save_corrected_path, "*ext.csv"))
    get_predictions(list_files, bmdn=bmdn, rf=rf, flex=flex, correct_ext_model = correct_ext_model, replace=replace)