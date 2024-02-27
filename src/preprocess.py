import os
import sys
import glob
import logging
import warnings

import numpy as np
import pandas as pd
from tqdm import tqdm
from astropy.io import fits
from astropy.table import Table
from astropy.utils.exceptions import AstropyWarning

from auxiliary.correct_extinction import correction
from auxiliary.paths import logs_path, save_corrected_path, save_xmatch_path
from auxiliary.columns import create_colors, calculate_colors, aper, splus, wise, galex, error_splus


warnings.simplefilter('ignore', category=AstropyWarning)
logging.basicConfig(filename=os.path.join(logs_path,'errors_field.log'), format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG, filemode='a')

first_error = True


def parse_args():
    verbose = False
    replace = False

    for arg in sys.argv:
        if arg == "--verbose":
            verbose = True
        elif arg == "--replace":
            replace = True
    return verbose, replace


def handle_exception(e, file):
    print(e)
    logging.error(e)
    logging.error("get_data FAILED for field %s." % file.split(os.path.sep)[-1])
    # add path to preprocess_fields_with_error.log:
    global first_error
    if first_error: 
        with open(os.path.join(logs_path, 'preprocess_fields_with_error.log'), 'w') as log:
            log.write(file+'\n')
        first_error = False
    else:
        with open(os.path.join(logs_path, 'preprocess_fields_with_error.log'), 'a') as log:
            log.write(file+'\n')

    return


def prep_wise(dataframe:pd.DataFrame):
    df = dataframe.copy()
    df["FW1"] = df["FW1"].replace(0, np.nan)
    df["FW2"] = df["FW2"].replace(0, np.nan) #there are negative values in crossmatch that will return RuntimeWarning: invalid value encountered in log10
    #replace any negative value
    
    
    df["W1"] = 22.5 - 2.5 * np.log10(df["FW1"])
    df["W2"] = 22.5 - 2.5 * np.log10(df["FW2"])
    return df


def handle_galex(dataframe:pd.DataFrame):
    input_value = 99
    try:
        dataframe[galex]
    except:
        for col in galex:
            dataframe[col] = input_value
    return dataframe


def missing_input(dataframe:pd.DataFrame):
    input_value = 99
    df = dataframe.copy()
    
    df[wise+galex] = df[wise+galex].fillna(value=input_value)
    len_original = len(df)

    #drop rows that all S-PLUS bands are NaN:
    df.dropna(subset=splus, how="all", inplace=True)
    len_dropped = len(df)
    if len_original-len_dropped > 0:
        if verbose: print(f"Dropped {len_original-len_dropped} rows with NaN in all S-PLUS bands")
        logging.info(f"Dropped {len_original-len_dropped} rows with NaN in all S-PLUS bands")

    return df


def process_data(filename, save=False, replace=False, verbose=True):
    if verbose:
        print(filename.split(os.path.sep)[-1])
    #logging.info("Starting for FIELD: %s" % filename.split(os.path.sep)[-1])
    save_filename = filename.split(os.path.sep)[-1].split('_')[0]+"_QSOz_VAC_preprocessed.csv"

    if os.path.exists(os.path.join(save_xmatch_path, save_filename)) and replace==False:
        if verbose:
            print("Preprocessed data file already exists. Passing.")
        return
    
    if os.path.exists(os.path.join(save_xmatch_path, save_filename)) and replace==True:
        if verbose:
            print("Preprocessed data file already exists. It is being replaced.")

    pos_splus = ["ID", "RA", "DEC"]
    
    try:
        f= fits.open(filename)
        table = np.lib.recfunctions.drop_fields(f[1].data, 'CV')
        table = Table(table)
        table = table.to_pandas()
        table["ID"] = table["ID"].str.decode('utf-8') 
        
    except Exception as e:
        handle_exception(e,filename)
        return
    
    table = handle_galex(table)
    table = prep_wise(table)

    try:
        table = correction(table)
    except Exception as e:
        handle_exception(e,filename)
        return
    
    table = missing_input(table)


    table = calculate_colors(table, broad=True, narrow=True, wise=True, galex=True)
    features = create_colors(broad=True, narrow=True, wise=True, galex=True)

    if save:
        table[pos_splus+features+splus+wise+galex+error_splus].to_csv(os.path.join(save_corrected_path, save_filename), index=False)
    
    return table[features]


# def process_data(filename, correct_ext=True, save=False, replace=False):
#     print(filename.split(os.path.sep)[-1])
#     #logging.info("Starting for FIELD: %s" % filename.split(os.path.sep)[-1])
#     if correct_ext:
    #         save_filename = filename.split(os.path.sep)[-1].split('_')[0]+"_QSOz_VAC_ext.csv"
    #     else:
    #         save_filename = filename.split(os.path.sep)[-1].split('_')[0]+"_QSOz_VAC.csv"

#     if os.path.exists(os.path.join(save_xmatch_path, save_filename)) and replace==False:
#         print("Preprocessed data file already exists. Passing.")
#         return
#     if os.path.exists(os.path.join(save_xmatch_path, save_filename)) and replace==True:
#         print("Preprocessed data file already exists. It is being replaced.")

#     pos_splus = ["ID", "RA", "DEC"]
    
#     try:
#         table = Table.read(filename)
#         table = table.to_pandas()
#         table["ID"] = table["ID"].str.decode('utf-8') 
#     except Exception as e:
#         handle_exception(e,filename)
#         return

#     table['W1_MAG'] = 22.5 - 2.5*np.log10(table['FW1']) # + 2.699
#     table['W2_MAG'] = 22.5 - 2.5*np.log10(table['FW2']) # + 3.339

#     # http://doxygen.lsst.codes/stack/doxygen/x_masterDoxyDoc/namespacelsst_1_1afw_1_1image.html#a0a023f269211d52086723788764d484e
#     # return std::abs(fluxErr / (-0.4 * flux * std::log(10)));
#     table['e_W1_MAG'] = abs(table['e_FW1'] / (-0.4*table['FW1']*np.log(10)))
#     table['e_W2_MAG'] = abs(table['e_FW2'] / (-0.4*table['FW2']*np.log(10)))

#     table['W1_MAG'].replace([np.inf, -np.inf], np.nan, inplace=True)
#     table['W2_MAG'].replace([np.inf, -np.inf], np.nan, inplace=True)

#     table[wise+galex] = table[wise+galex].fillna(value=99)
#     table.dropna(subset=splus, inplace=True)
#     # table[wise] = table[wise].replace(-1, val_mb)

#     try:
#         if correct_ext:
#             table = correction(table)
#     except Exception as e:
#         handle_exception(e,filename)
#         return

#     table = calculate_colors(table, broad=True, narrow=True, wise=True, galex = True, aper=aper)
#     features = create_colors(broad=True, narrow=True, wise=True, galex=True, aper=aper)
    
#     #logging.info("Finished preprocessing dataset.")

#     if save:
#         table[pos_splus+features+splus+wise+galex+error_splus].to_csv(os.path.join(save_corrected_path, save_filename), index=False)
#         print("Saved file.")
    
#     return table[features]


def get_data(list_input, save=True, replace= False, verbose=True):
    logging.info("get_data was called for %s fields." % len(list_input))
    for file in tqdm(list_input):
        process_data(file,  save=save, replace=replace, verbose=verbose)
    return


if __name__ == "__main__":
    logging.info("preprocess.py was called.")
    verbose, replace = parse_args()
    list_input = glob.glob(os.path.join(save_xmatch_path, "*.fits"))
    get_data(list_input, save = True, replace = replace, verbose=verbose)
    if first_error: #if didnt enter handle_error, then first_error is still True
        os.remove(os.path.join(logs_path, 'preprocess_fields_with_error.log'))
