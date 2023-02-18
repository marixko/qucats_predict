import os

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

if maua_server:
    raw_path = "/storage/splus/Catalogues/iDR4/VAC_features"
    results_path = "/storage/splus/Catalogues/VACs/qso_z/iDR4"
else:
    # raw
    raw_path = os.path.join(data_path, 'raw')
    # results
    results_path = os.path.join(data_path, 'result')

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
# auxiliary
aux_path = os.path.join(codes_path, 'auxiliary')

