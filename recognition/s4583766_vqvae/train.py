'''
Training script for the model, including validation, testing, and saving of the model.
Imports the model from modules.py, and the data loader from dataset.py. 
Plots losses and metrics observed during training. 

Sophie Bates, s4583766.
'''

import os

import dataset
import modules
import numpy as np
import torch
import torchvision
from dataset import load_dataset
from modules import VQVAE, Decoder, Encoder

# Setup file paths
PATH = os.getcwd() + '/'
DATA_PATH_TRAINING_RANGPUR = '/home/groups/comp3710/OASIS'
DATA_PATH_TRAINING_LOCAL = PATH + 'test_img/'
BATCH_SIZE = 32

# Set the mode to either 'rangpur' or 'local' for testing purposes
mode = 'local'
if mode == 'rangpur':
	data_path_training = DATA_PATH_TRAINING_RANGPUR
elif mode == 'local':
	data_path_training = DATA_PATH_TRAINING_LOCAL

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if not torch.cuda.is_available():
    print("Warning CUDA not Found. Using CPU...")

# Hyper-parameters
learning_rate = 3e-4

load_dataset(data_path_training, BATCH_SIZE)

vqvae = VQVAE(256, 512, 64).to(device)

