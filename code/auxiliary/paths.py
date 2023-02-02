import os


mycwd = os.path.abspath(os.getcwd())
os.chdir('..')
back_cwd = os.path.abspath(os.getcwd())
os.chdir(mycwd)

# data
data_path = os.path.join(back_cwd, 'data')

# raw
raw_data = os.path.join(data_path, 'raw')

# input_model
input_data = os.path.join(data_path, 'input_model')

# model
model_path = os.path.join(back_cwd, 'trained_model')

# results
# results_path = os.path.join(back_cwd, 'results')
