import os
from tqdm import tqdm
import glob
import logging
from auxiliary.paths import raw_path, logs_path, save_xmatch_path
from auxiliary.crossmatch import match_stilts

logging.basicConfig(filename=os.path.join(logs_path,'field_error.log'), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG, filemode='a')

def get_crossmatch(list_raw, replace=False, diff = True):
    logging.info("get_crossmatch was called for %s fields." % len(list_raw))
    
    if diff:
        replace = False #Only crossmatch fields that have not been crossmatched yet.
        list_match = glob.glob(os.path.join(save_xmatch_path, "*features.fits"))
        list_match = [os.path.basename(x) for x in list_match]
        list_raw = [os.path.basename(x) for x in list_raw]
        list_diff = list(set(list_raw) - set(list_match))
        list_raw = [os.path.join(raw_path, x) for x in list_diff]
        
    
    for file in tqdm(list_raw):
        try:
            match_stilts(file, replace)
        except:
            logging.error("match_stilts FAILED for field %s." % file.split(os.path.sep)[-1])
            continue
    return

if __name__ == "__main__":
    logging.info("get_crossmatch.py was called.")
    replace = False
    list_raw = glob.glob(os.path.join(raw_path, "*features.fits"))
    get_crossmatch(list_raw, replace=replace, diff = True)
