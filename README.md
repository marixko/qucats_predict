# Quasar photometric redshifts for S-PLUS 

This repository contains the source codes to estimate photometric redshifts for quasars using the S-PLUS photometry. 
 We provide single-point estimates for the photometric redshifts using three different methods: Random Forest, Bayesian Mixture Density Model, and FlexCoDE (plus, the average between all three methods). Probability density functions (PDFs) are also provided but only for the Bayesian Mixture Density Model and FlexCoDE. 


The accompanying paper is Nakazono & Valença et al. (submitted). Link to the paper will be provided as soon as it is published. There one can find details about the data, methods and the expected performances.

The repository is organized as follows:

- `data/`: contains the dustmaps used for the extinction correction.
- `src/`: contains the source codes to estimate the photometric redshifts.
- `final_model`: contains the trained models for the Random Forest, Bayesian Mixture Density Model, and FlexCoDE. The codes to train the models are provided in a separate repository.
- `logs/`: contains the logs of the photometric redshifts estimation.


# Versions and dependencies
Codes were written in:
- Python 3.7.16 for Random Forest (`environment.yml`)
- Python 3.8.18 for Bayesian Mixture Density Model (`bmdn_env.yml`)
- R 4.2.2 for FlexCoDE

# Steps of the pipeline
At this moment, the pipeline is designed to run each method separately (although one can call all of them at once) for debugging purposes. Therefore, each step is saving an output file. This should be improved in the future. 

The pipeline is divided into four main steps that should be run in the following order for **each S-PLUS field**:

1) get_crossmatch.py
2) preprocess.py
3) get_predictions.py
4) merge_catalogs.py


## Step 1: get_crossmatch.py
This code is used to crossmatch the S-PLUS catalog with the unWISE and GALEX catalogs. For this step, stilts.jar is needed. Output is a.fits file with the crossmatched catalogs. This step can be skipped if the crossmatched catalog is already available.
This step is implemented to run in a pre-defined folder at S-PLUS's server that contains the `*VAC_features.fits` files for each S-PLUS field. 

## Step 2: preprocess.py
This code is used to preprocess the data using output from Step 1 as input. It includes the following steps:
- Load the crossmatched catalog
- Handle missing-band values (fill with 99)
- Apply extinction correction
- Calculate features (colors) that are used to estimate the photometric redshifts
- Save the preprocessed catalog

## Step 3: get_predictions.py
This code is used to estimate the photometric redshifts using output from Step 2 as input. It includes the following steps:
- Load the preprocessed catalog
- Load the trained models
- Estimate the photometric redshifts
- Save the photometric redshifts and the probability density functions (PDFs)

## Step 4: merge_catalogs.py
This code is used to merge the output of each method obtained from Step 3 in a single .csv file. 



# Examples of usage

To run the pipeline, one should use the following commands:

```bash
python get_crossmatch.py 
python preprocess.py
python get_predictions.py --rf --bmdn --flexcode
python merge_catalogs.py 
```

Parsed arguments are: 
- --verbose: to print the logs
- --replace: to replace the output files if they already exist. Skip if it exists.
- --rf: to run the Random Forest method [only for `get_predictions.py`]
- --bmdn: to run the Bayesian Mixture Density Model [only for `get_predictions.py`]
- --flexcode: to run the FlexCoDE method [only for `get_predictions.py`]
- --diff: to run code only for files that do not have output files yet [only for `get_crossmatch.py` but can be implemented for the other codes as well]
- --remove: to remove the output file for each method after merging them in a single file. [only for `merge_catalogs.py`]

# Important Notes
- The pipeline is designed to run in S-PLUS's server and for S-PLUS DR4. For any other data release, the trained models would likely need to retrained.
- Large files (such as some trained models) are not being pushed to the repository. Please contact the authors if you need access to these files.
- This implementation are intend to work in S-PLUS' server only and its current pattern of data release directories. If you want to use it locally, you will need to adapt the code (e.g. paths) to your own data structure.

# Codes were written by
- Lilianne Nakazono
- Raquel Valença
- Rafael Izbicki
- Gabriela Soares

Feel free to open a pull request or an issue. This repository is under development and we are open to suggestions and improvements. 

# How to cite
If you use this code, please cite the paper Nakazono & Valença et al. (submitted). Full reference will be provided as soon as it is published.

# Contact
If you have any questions, please contact Lilianne Nakazono or Raquel Valença

