import os
import sys
import glob
import logging
import pandas as pd
from tqdm import tqdm
from timeit import default_timer as timer
from datetime import timedelta
from auxiliary.paths import results_path, logs_path

logging.basicConfig(filename=os.path.join(logs_path,'merge_catalogs.log'), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG, filemode='a')

def parse_args():
    verbose = False
    replace = False
    remove = False

    for arg in sys.argv:
        if arg == "--verbose":
            verbose = True
        elif arg == "--replace":
            replace = True
        elif arg == "--remove":
            remove = True
    return verbose, replace, remove

def merge_catalogs(list_files, verbose=True, replace=False, remove=True):
    start_time = timer()
    logging.info("Function merge_catalogs was called. Loop has %s fields" % len(list_files))

    for file in tqdm(list_files):
        filename = file.split(os.path.sep)[-1].split("_")[0]
        filename = filename + "_QSOz_VAC_ext.csv"
        logging.info("Starting for FIELD: %s" % filename)
        if verbose:
            print(filename)

        if os.path.exists(os.path.join(results_path, filename)):
            if verbose:
                print("Master catalogue already exists for this field.")
            if replace==False:
                logging.warning("Master catalogue already exists for this field. Passing...")
                continue
            else:
                if verbose:
                    print("Replacing file...")
                logging.info("Master catalogue already exists for this field. It is being replaced.")

        if os.path.exists(os.path.join(results_path, filename.split('.')[0]+"_bmdn.csv"))==False:
            if verbose:
                print("BMDN predictions file is not in folder. Failed to create a catalog for this field.")
            logging.error("BMDN predictions file is not in folder. FAILED to create a catalog for this field.")
            continue

        if os.path.exists(os.path.join(results_path, filename.split('.')[0]+"_flex.csv"))==False:
            if verbose:
                print("FlexCoDE predictions file is not in folder. Failed to create a catalog for this field. ")
            logging.error("FlexCoDE predictions file is not in folder. FAILED to create a catalog for this field.")
            continue

        try:
            bmdn = pd.read_table(os.path.join(results_path, filename.split('.')[0]+"_bmdn.csv"), sep=",")
            flex = pd.read_table(os.path.join(results_path, filename.split('.')[0]+"_flex.csv"), sep=",")
            rf =  pd.read_table(os.path.join(results_path, filename.split('.')[0]+"_rf.csv"), sep=",")

            table = pd.concat([rf, bmdn["z_bmdn_peak"], flex["z_flex_peak"]], axis=1)
            table["z_mean"] = table[["z_rf", "z_bmdn_peak", "z_flex_peak"]].mean(axis=1, numeric_only=True)
            table["z_std"] = table[["z_rf", "z_bmdn_peak", "z_flex_peak"]].std(axis=1, numeric_only=True)

            table = pd.concat([table, bmdn.iloc[:,4:], flex.iloc[:,4:]], axis=1)
            
            table.to_csv(os.path.join(results_path, filename), index=False)
        except:
            logging.error("FAILED to save final catalog for this field.")
            continue

        if remove:
            os.system(f"""rm {os.path.join(results_path, filename.split('.')[0]+"_*")}""")
            logging.info("Removed rf, bmdn and flex result files for this field.")

    end_time = timer()
    if verbose:
        print("Finished process. Total elapsed time: %s" % timedelta(seconds=end_time-start_time))
    logging.info("Finished process in %s" % timedelta(seconds=end_time-start_time))
    
    return

if __name__=="__main__":
    logging.info("merge_catalogs.py was called.")
    verbose, replace, remove = parse_args()
    list_files = glob.glob(os.path.join(results_path, "*ext_rf.csv"))
    merge_catalogs(list_files, verbose=verbose, replace=replace, remove=remove)