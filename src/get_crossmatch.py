import os
import sys
import glob
import logging

import pandas as pd
from tqdm import tqdm

from auxiliary.paths import raw_path, logs_path, save_xmatch_path
from auxiliary.crossmatch import match_stilts


logging.basicConfig(filename=os.path.join(logs_path,'field_error.log'), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG, filemode='a')


def parse_args():
    verbose = False
    replace = False
    diff = False

    for arg in sys.argv:
        if arg == "--verbose":
            verbose = True
        elif arg == "--replace":
            replace = True
        elif arg == "--diff":
            diff = True
    return verbose, replace, diff


def get_crossmatch(list_raw, replace=False, diff = True):
    logging.info("get_crossmatch was called for %s fields." % len(list_raw))
    
    if diff:
        replace = False #Only crossmatch fields that have not been crossmatched yet.
        list_match = glob.glob(os.path.join(save_xmatch_path, "*features.fits")) #List of fields that have been crossmatched.
        list_match = [os.path.basename(x) for x in list_match]
        list_raw = [os.path.basename(x) for x in list_raw] #List of fields in the original folder (after calibration, before crossmatch).
        list_diff = list(set(list_raw) - set(list_match)) #List of fields that have not been crossmatched yet.
        list_raw = [os.path.join(raw_path, x) for x in list_diff] # Full path of fields that have not been crossmatched yet.
    
    for file in tqdm(list_raw):
        try:
            match_stilts(file, replace)
        except:
            logging.error("match_stilts FAILED for field %s." % file.split(os.path.sep)[-1])
            continue
    return


if __name__ == "__main__":
    logging.info("get_crossmatch.py was called.")
    # replace = True
    verbose, replace, diff = parse_args()
    # list_raw = glob.glob(os.path.join(raw_path, "*features.fits"))

    list_raw = pd.read_csv("/storage/splus/scripts/qso_z/logs/preprocess_fields_with_error.log")
    list_raw = list_raw.iloc[:,0].to_list()
    list_raw = [os.path.join(raw_path, x.split(os.sep)[-1]) for x in list_raw]
    print(list_raw)
    
    get_crossmatch(list_raw, replace=replace, diff = False)
