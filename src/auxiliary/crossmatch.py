import os
import logging
import subprocess

from auxiliary.paths import logs_path,  aux_path, save_xmatch_path


logging.basicConfig(filename=os.path.join(logs_path,'errors_field.log'), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG, filemode='a')


def match_stilts(filename, replace=True, verbose=True):
    galex_failed = False
    input_filename = filename
    file = os.path.basename(input_filename)

    galex_filename = os.path.join(save_xmatch_path, file.split('.')[0]+"_temp.fits")

    final_filename = os.path.join(save_xmatch_path,file)
    
    if os.path.exists(final_filename) and replace==False:
        if verbose:
            print("Crossmatch file already exists. Passing.")
        logging.warning("Crossmatch file already exists. Passing.")
        return
    try:
        os.system(f"""java -jar {os.path.join(aux_path,"stilts.jar")} cdsskymatch in={input_filename} cdstable=II/335/galex_ais ra=RA dec=DEC radius=2 find=each blocksize=100000 \\
                ocmd='addcol ID_GALEX "objid"; addcol sep_GALEX "angDist"; delcols "objid angDist"' out={galex_filename}""")
    except:
        pass
    
    if os.path.exists(galex_filename) == False:
        if verbose:
            print("GALEX crossmatch failed. Passing to unWISE.")
        logging.warning("GALEX crossmatch failed. Passing to unWISE.")
        galex_failed = True

    
    if galex_failed:
        if verbose:
            print("Matching with unWISE.")
        os.system(f"""java -jar {os.path.join(aux_path,"stilts.jar")} cdsskymatch in={input_filename} cdstable=II/363/unwise ra=RA dec=DEC radius=2 find=each blocksize=100000 \\
                    ocmd='addcol ID_unWISE "objID"; addcol sep_unWISE "angDist"; delcols "objID angDist"' out={final_filename}""")

    else:
        os.system(f"""java -jar {os.path.join(aux_path,"stilts.jar")} cdsskymatch in={galex_filename} cdstable=II/363/unwise ra=RA dec=DEC radius=2 find=each blocksize=100000 \\
                    ocmd='addcol ID_unWISE "objID"; addcol sep_unWISE "angDist"; delcols "objID angDist"' out={final_filename}""")
        os.system(f"""rm {galex_filename}""")

    if verbose:
        print("Finished crossmatching.")
    return
