import os
import glob
import logging
import numpy as np
import pandas as pd
import warnings
from tqdm import tqdm
from astropy.table import Table
from auxiliary.paths import input_path, logs_path, save_corrected_path, save_xmatch_path
from auxiliary.columns import create_colors, calculate_colors, wise, splus, galex, error_splus
from auxiliary.correct_extinction import correction
from astropy.utils.exceptions import AstropyWarning

warnings.simplefilter('ignore', category=AstropyWarning)

logging.basicConfig(filename=os.path.join(logs_path,'errors_field.log'), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG, filemode='a')

def process_data(filename, correct_ext=True, save=False, replace=False):
    print(filename.split(os.path.sep)[-1])
    #logging.info("Starting for FIELD: %s" % filename.split(os.path.sep)[-1])
    if correct_ext:
        save_filename = filename.split(os.path.sep)[-1].split('_')[0]+"_QSOz_VAC_ext.csv"
    else:
        save_filename = filename.split(os.path.sep)[-1].split('_')[0]+"_QSOz_VAC.csv"

    if os.path.exists(os.path.join(save_xmatch_path, save_filename)) and replace==False:
        print("Preprocessed data file already exists. Passing.")
        return
    if os.path.exists(os.path.join(save_xmatch_path, save_filename)) and replace==True:
        print("Preprocessed data file already exists. It is being replaced.")

    pos_splus = ["ID", "RA", "DEC"]
    
    try:
        table = Table.read(filename)
        table = table.to_pandas()
        table["ID"] = table["ID"].str.decode('utf-8') 
    except Exception as e:
        print(e)
        logging.error(e)
        return

    table['W1_MAG'] = 22.5 - 2.5*np.log10(table['FW1']) # + 2.699
    table['W2_MAG'] = 22.5 - 2.5*np.log10(table['FW2']) # + 3.339

    # http://doxygen.lsst.codes/stack/doxygen/x_masterDoxyDoc/namespacelsst_1_1afw_1_1image.html#a0a023f269211d52086723788764d484e
    # return std::abs(fluxErr / (-0.4 * flux * std::log(10)));
    table['e_W1_MAG'] = abs(table['e_FW1'] / (-0.4*table['FW1']*np.log(10)))
    table['e_W2_MAG'] = abs(table['e_FW2'] / (-0.4*table['FW2']*np.log(10)))

    table['W1_MAG'].replace([np.inf, -np.inf], np.nan, inplace=True)
    table['W2_MAG'].replace([np.inf, -np.inf], np.nan, inplace=True)

    table[wise+galex] = table[wise+galex].fillna(value=99)
    table.dropna(subset=splus, inplace=True)
    # table[wise] = table[wise].replace(-1, val_mb)

    try:
        if correct_ext:
            table = correction(table)
    except Exception as e:
        print(e)
        logging.error(e)
        return

    table = calculate_colors(table, broad=True, narrow=True, wise=True, galex = True, aper="PStotal")
    features = create_colors(broad=True, narrow=True, wise=True, galex=True, aper="PStotal")
    
    #logging.info("Finished preprocessing dataset.")

    if save:
        table[pos_splus+features+splus+wise+galex+error_splus].to_csv(os.path.join(save_corrected_path, save_filename), index=False)
        print("Saved file.")
    
    return table[features]

def get_data(list_input, correct_ext = True, save=True, replace= False):
    logging.info("get_data was called for %s fields." % len(list_input))
    logging.info("Parameter correct_ext = %s" % correct_ext)
    for file in tqdm(list_input):
        try:
            process_data(file, correct_ext = correct_ext, save=save, replace=replace)
        except:
            logging.error("get_data FAILED for field %s." % file.split(os.path.sep)[-1])
            continue
    return


if __name__ == "__main__":
    logging.info("preprocess.py was called.")
    replace = False
    correct_ext = True
    list_input = glob.glob(os.path.join(save_xmatch_path, "STRIPE*138**.fits"))
    print(list_input)
    get_data(list_input, correct_ext = correct_ext, save = True, replace = replace)
