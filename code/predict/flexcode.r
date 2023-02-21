library(FlexCoDE)
library(parallel)
# remotes::install_github("rstudio/reticulate")
# install.packages("reticulate",  repos = "http://cran.us.r-project.org")

library(reticulate)
reticulate::source_python(file.path(getwd(), "auxiliary", "paths.py"))

args <- commandArgs(trailingOnly = TRUE)
for (arg in args){
  if(arg=="--replace"){
    replace <- True
  }
}

correct_ext <- TRUE

fit0 <- readRDS(file.path(py$model_path, "flexcode","ext_fit2.rds"))
fit1 <- readRDS(file.path(py$model_path, "flexcode","ext_fit2_1.rds"))
fit2 <- readRDS(file.path(py$model_path, "flexcode","ext_fit2_2.rds"))
fit3 <- readRDS(file.path(py$model_path, "flexcode","ext_fit2_3.rds"))
fit4 <- readRDS(file.path(py$model_path, "flexcode","ext_fit2_4.rds"))
fits <- list(fit0,fit1,fit2,fit3,fit4)

if (correct_ext == TRUE) {
  file_list <- Sys.glob(file.path(py$save_corrected_path,"*ext.csv"))
} else {
  file_list <- Sys.glob(file.path(py$save_corrected_path, "*VAC.csv"))
}

########

get_filename <- function(path) {
    filename <- rev(setdiff(strsplit(path,"/|\\\\")[[1]], ""))
    filename <- setdiff(strsplit(filename,"\\.")[[1]], "")
    return(filename[1])
}

########

counter <- 1

flex_predict <- function(path_to_file, B = 200, correct_ext=TRUE, save=TRUE, replace=FALSE, verbose=TRUE){
  # B: number of grid points where the density will be evaluated

filename <- get_filename(path_to_file)
save_filepath <- file.path(py$results_path, paste0(filename, "_flex.csv"))
if(file.exists(save_filepath) & replace==FALSE){
  return()
}

if(verbose==TRUE){
cat("Running: ", filename)
cat("\n")
}
# Dataset with photometric information.
# Needs to contain the same photometric
#    features as colnames(fit0$xTrain)
data<-read.csv(path_to_file)

# Filter covariates (features)
data_cov <- data[,colnames(fit0$xTrain)]

# ID information
info <- data[,c("ID","RA","DEC")]

rm(data) #clean memory

# Remove missing data
# which_remove <- !complete.cases(data_cov)
# data_cov <- data_cov[!which_remove,]
# info <- info[!which_remove,]

# Compute estimated photo-z densities
pred <- array(NA,dim=c(length(fits),nrow(data_cov),B))
for(ii in seq_along(fits))
{
  pred[ii,,] <- predict(fits[[ii]],data_cov,B=B)$CDE
}
pred <- apply(pred, c(2,3), function(x) mean(x))
colnames(pred) <- paste0("z_flex_pdf_",1:B)

# add mode of the densities (z_peak), a point estimate of the redshift
grid <- predict(fits[[1]],data_cov[1,,drop=FALSE],B=B)$z
z_flex_peak <- grid[apply(pred,1,which.max)]
if (save==TRUE) {
  write.csv(cbind(info,z_flex_peak,pred), save_filepath ,row.names = FALSE)
} 

cat("Finished: ", filename)
}

mclapply(file_list, flex_predict, mc.cores=5L)
