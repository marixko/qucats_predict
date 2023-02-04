import os
import pickle
import pandas as pd
from auxiliary.columns import create_colors
from auxiliary.paths import input_path

def load_rf_model(filename):
    file = open(os.path.join(filename), 'rb')
    model = pickle.load(file)
    return model

def rf_predict(data, model):
    z = model.predict(data)
    return z

# data = pd.read_table(os.path.join(input_path, "STRIPE82-0170_QSOz_VAC.csv"))

# features = create_colors(broad=True, narrow=True, wise=True, galex=True, aper="PStotal")

# print(data[features])
