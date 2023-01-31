import os
from time import sleep
from threading import Thread

import numpy as np

from auxiliary.paths import results_path, data_path
from bmdn.final_predict import PredictForFileNoTry

correct_ext = True
s = '-ext' if correct_ext else ''
folders = {'model': os.path.join(results_path, f'final_model{s}', ''),
            'input': os.path.join(data_path, 'input'),
            'output': os.path.join(data_path, 'output')}

All_Files = [s.replace('.csv', '') for s in os.listdir(folders['input'])]
Predicted_Files = [s.replace('.csv', '') for s in os.listdir(folders['output'])]
Files = np.setdiff1d(All_Files, Predicted_Files) # Fields that will be predicted

Files_to_predict_parallel = 2
Threads = np.arange(0, len(Files)+1, 1)

Processes = {}
for i in range(len(Threads)-1):
    Processes[i] = Thread(target=PredictForFileNoTry,
                            args=(Files[Threads[i]:Threads[i+1]], folders))

for lista in np.array_split(np.arange(0, len(Threads)-1), np.ceil(len(Threads)/Files_to_predict_parallel)):
    for i in lista:
        Processes[i].start()
        sleep(1.5)

    for i in lista:
        Processes[i].join()
