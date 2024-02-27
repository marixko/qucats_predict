import os
import sys
import glob
import logging
from pickle import load
from datetime import timedelta
from timeit import default_timer as timer

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from tqdm import tqdm
from pandas import read_table
from joblib import load as job_load
from tensorflow.keras.models import load_model

from auxiliary.columns import convert_f64_to_f32, create_colors
from predict.bmdn import preprocess_BMDN, FinalPredict
from auxiliary.paths import results_path, model_path, predict_path, logs_path, save_corrected_path


logging.basicConfig(filename=os.path.join(logs_path, 'get_predictions.log'),
                    format='%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG, filemode='a')


def parse_args():
    
    rf = False
    bmdn = False
    flex = False
    replace = False
    verbose = False
    for arg in sys.argv:
        if arg == "--rf":
            rf = True
        elif arg == "--bmdn":
            bmdn = True
        elif arg == "--flex":
            flex = True
        elif arg == "--replace":
            replace = True
        elif arg == "--verbose":
            verbose = True
    return rf, bmdn, flex, replace, verbose


def handle_error_file(e, file, verbose):
    if verbose: print(file, e)
    logging.error("Error in file %s." % file.split(os.path.sep)[-1])
    logging.error(e)
    return


def handle_error_general(e, verbose):
    if verbose: print(e)
    logging.error(e)
    return


def get_predictions(list_files, bmdn=True, rf=True, flex=True, replace=False, verbose=True):
    start_time = timer()

    if verbose:
        print(f"Starting predictions for {len(list_files)} files")
        print("Warning: if the result files already exists, they will be replaced by default for now (bmdn and rf)! ")
        
    model = {}

    try:
        
        if bmdn:
            
            bmdn_path = os.path.join(model_path, "bmdn", "final_model_dr4_BNWG_linux_700e")  # adjust model filename!
            model["bmdn"] = load_model(os.path.join(bmdn_path, "SavedModels", "Fold0"), compile=False)
            
            Scaler_1 = job_load(os.path.join(bmdn_path, 'Scaler_1_Quantile.joblib'))
            Scaler_2 = job_load(os.path.join(bmdn_path, 'Scaler_2_MinMax.joblib'))
            with open(os.path.join(bmdn_path, 'Model_Summary.txt'), 'r') as summary_file:
                bmdn_features = eval(summary_file.readlines()[-1])
            
            bmdn_columns = ['ID', 'RA', 'DEC', 'z_bmdn_peak', 'n_peaks_bmdn']
            for i in range(1, 8):
                bmdn_columns.append(f'z_bmdn_pdf_weight_{i}')
                bmdn_columns.append(f'z_bmdn_pdf_mean_{i}')
                bmdn_columns.append(f'z_bmdn_pdf_std_{i}')
            
    except Exception as e:
        handle_error_general(e, verbose)
        pass

    try:
        
        if rf:
            rf_features = create_colors(broad=True, narrow=True, wise=True, galex=True)
            rf_path = os.path.join(model_path, "rf")
            model["rf"] = load(open(os.path.join(rf_path, "RF_final_broad+GALEX+WISE+narrow.sav"), 'rb'))  # adjust model filename!
    
    except Exception as e: 
        handle_error_general(e, verbose)
        pass

    if rf or bmdn: 
        for file in tqdm(list_files):
            save_filename = file.split(os.path.sep)[-1].split('.')[0]
            logging.info(f"Starting for FIELD: {save_filename}")
            if verbose: print(f"Starting for field: {save_filename}")
            table = read_table(file, sep=",")

            table = table.reset_index(drop=True)
            
            try:
                if bmdn:
                    save_path_bmdn = os.path.join(results_path, save_filename+"_bmdn.csv")
                    if os.path.exists(save_path_bmdn) and replace==False:
                        continue
                    if verbose: print("Calculating BMDN predictions...")
                    
                    chunk_bmdn = table.copy(deep=True)
                    sample, features = preprocess_BMDN(chunk_bmdn, bmdn_features, Scaler_1, Scaler_2)
                    Result_DF = FinalPredict(model["bmdn"], sample, features)
                    convert_f64_to_f32(Result_DF[bmdn_columns]).to_csv(save_path_bmdn, index=False)
                        
            except Exception as e:
                handle_error_file(e, file, verbose)
                pass

            try:
                if rf:
                    save_path_rf = os.path.join(results_path, save_filename+"_rf.csv")
                    if os.path.exists(save_path_rf) and replace==False:
                        continue
                    
                    if verbose: print("Calculating RF predictions...")

                    z = model["rf"].predict(table[rf_features])
                    table["z_rf"] = z
                    convert_f64_to_f32(table[["ID", "RA",  "DEC", "z_rf"]]).to_csv(save_path_rf, index=False)
                    
            except Exception as e:
                handle_error_file(e, file, verbose)
                pass

    try:
        if flex:
            if verbose: print("Calculating FlexCoDE predictions...")
            flex_path = os.path.join(predict_path, "flexcode.r")
            os.system(f"""export MKL_SERVICE_FORCE_INTEL=1""")
            cmd_r = f"""Rscript {flex_path}"""
            if replace: cmd_r = f"""Rscript {flex_path} --replace"""
            os.system(cmd_r)
            
    except Exception as e:
        handle_error_general(e, verbose)
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

    if verbose: print(f"Finished process. Total elapsed time: {timedelta(seconds=end_time-start_time)}")
    
    return


if __name__ == "__main__":
    logging.info("get_predictions.py was called.")
    
    rf, bmdn, flex, replace, verbose = parse_args()
    list_files = glob.glob(os.path.join(save_corrected_path, "*preprocessed.csv"))
    
    get_predictions(list_files, bmdn=bmdn, rf=rf, flex=flex, replace=replace, verbose=verbose)
