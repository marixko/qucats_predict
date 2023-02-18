import os

def check_dir(path:str):
    """check_dir will check if directories already exists. If not, it will create the directory (only necessary substructures)

    Parameters
    ----------
    path : str
        path that will be checked if it already exists
    """
    if not os.path.exists(path):
        os.makedirs(path)
    return

maua_server=False
mycwd = os.path.abspath(os.getcwd())
if mycwd.split(os.sep)[-1] == "qucats_predict": #folder name in Maua server is qso_z and not qucats_predict
    parent_cwd = mycwd
    codes_path = os.path.join(parent_cwd,"code")
if mycwd.split(os.sep)[-1] == "code":
    # os.chdir('..')
    codes_path = os.path.abspath(os.getcwd())
    os.chdir('..')
    parent_cwd = os.path.abspath(os.getcwd())
    os.chdir(mycwd)
    if parent_cwd.split(os.path.sep)[-1] == "qso_z":
        maua_server=True

# data
data_path = os.path.join(parent_cwd, 'data')
# input_model
input_path = os.path.join(data_path, 'input')
# model
model_path = os.path.join(parent_cwd, 'final_model')
# predict
predict_path = os.path.join(codes_path, 'predict')
# logs
logs_path = os.path.join(parent_cwd, 'logs')
check_dir(logs_path)
# auxiliary
aux_path = os.path.join(codes_path, 'auxiliary')

if maua_server:
    raw_path = "/storage/splus/Catalogues/iDR4/VAC_features/original"
    results_path = "/storage/splus/Catalogues/VACs/qso_z/iDR4"
    save_xmatch_path = "/storage/splus/Catalogues/iDR4/VAC_features/corrected_qso_z"
    save_corrected_path = save_xmatch_path

else:
    # raw
    raw_path = os.path.join(data_path, 'raw')
    # results
    results_path = os.path.join(data_path, 'result')
    check_dir(results_path)
    save_xmatch_path = input_path
    save_corrected_path = input_path


