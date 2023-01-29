import os


mycwd = os.path.abspath(os.getcwd())
os.chdir('..')
back_cwd = os.path.abspath(os.getcwd())
os.chdir(mycwd)

# data
data_path = os.path.join(back_cwd, 'data')

# results
results_path = os.path.join(back_cwd, 'results')
