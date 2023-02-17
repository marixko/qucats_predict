import os
import logging
from auxiliary.paths import input_path, logs_path, codes_path

logging.basicConfig(filename=os.path.join(logs_path,'get_predictions.log'), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG, filemode='a')

def match_stilts(filename, replace=True):
    input_filename = filename
    file = filename.split(os.path.sep)[-1]
    # input_filename = os.path.join(raw_path,filename)
    # input_filename = input_filename.replace(" ", "\ ")

    galex_filename = os.path.join(input_path, file.split('.')[0]+"_temp.fits")
    # galex_filename = filename.split('.')[0]+"_temp.fits"
    # galex_filename = galex_filename.replace(" ", "\ ")
    
    final_filename = os.path.join(input_path,file)
    
    if os.path.exists(final_filename) and replace==False:
        logging.warning("Crossmatch file already exists. Passing.")
        return
            
    os.system(f"""java -jar {os.path.join(codes_path,"stilts.jar")} cdsskymatch in={input_filename} cdstable=II/335/galex_ais ra=RA dec=DEC radius=2 find=each blocksize=100000 \\
                ocmd='addcol ID_GALEX "objid"; addcol sep_GALEX "angDist"; delcols "objid angDist"' out={galex_filename}""")
    

    # output_filename = output_filename.replace(" ", "\ ")
    os.system(f"""java -jar {os.path.join(codes_path,"stilts.jar")} cdsskymatch in={galex_filename} cdstable=II/363/unwise ra=RA dec=DEC radius=2 find=each blocksize=100000 \\
                ocmd='addcol ID_unWISE "objID"; addcol sep_unWISE "angDist"; delcols "objID angDist"' out={final_filename}""")
    os.system(f"""rm {galex_filename}""")

    logging.info("Finished crossmatching.") 
    return
