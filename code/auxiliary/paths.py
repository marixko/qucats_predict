import os

mycwd = os.path.abspath(os.getcwd())
if mycwd.split(os.sep)[-1] == "qucats_predict":
    parent_cwd = mycwd
    codes_path = os.path.join(parent_cwd,"code")
if mycwd.split(os.sep)[-1] == "code":
    # os.chdir('..')
    codes_path = os.path.abspath(os.getcwd())
    os.chdir('..')
    parent_cwd = os.path.abspath(os.getcwd())
    os.chdir(mycwd)

# data
data_path = os.path.join(parent_cwd, 'data')

# raw
raw_path = os.path.join(data_path, 'raw')

# input_model
input_path = os.path.join(data_path, 'input')

# model
model_path = os.path.join(parent_cwd, 'final_model')

# results
results_path = os.path.join(data_path, 'result')

# predict
predict_path = os.path.join(codes_path, 'predict')

# logs

logs_path = os.path.join(parent_cwd, 'logs')