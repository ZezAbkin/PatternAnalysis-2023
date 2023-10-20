##################################
#
# Author: Joshua Wallace
# SID: 45809978
#
###################################

import torch
import time
import torch.nn as nn
import torch.nn.functional as F
from dataset import Dataset
import matplotlib.pyplot as plt
from utils import PRINT_AT, DEVICE, NOISE
from abc import ABC, abstractmethod

class Trainer(ABC) :
    """
    Interface for the required methods to be implemented on a trainer.
    """
    def __init__(self, model: nn.Module, dataset: Dataset, lr=1e-3, wd=0, epochs=10, savepath='./models/vqvae') :
        self.savepath = savepath
        self.lr = lr
        self.wd = wd
        self.epochs = epochs
        self.model = model.to(DEVICE)
        self.dataset = dataset
    
    @abstractmethod
    def train(self) -> None :
        pass

    @abstractmethod
    def validate(self) -> None :
        pass

    @abstractmethod
    def plot(self, save = True, show = True) -> None :
        pass


class TrainVQVAE(Trainer) :
    
    def __init__(self, model: nn.Module, dataset: Dataset, lr=1e-3, wd=0, epochs=10, savepath='./models/vqvae') :
        super().__init__(model, dataset, lr, wd, epochs, savepath)
        self.optimiser = torch.optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=self.wd)        
        self.total_losses = list()
        self.quant_loss = list()
        self.recon_loss = list()


    def train(self) -> None :
        if self.dataset.train_unloaded() :
            self.dataset.load_train()
        
        self.model.train()
        start = time.time()
        for epoch in range(self.epochs) :
            for i, (data, label) in enumerate(self.dataset.get_train()) :
                data = data.to(DEVICE)
                self.optimiser.zero_grad()

                embedding_loss, x_hat, perplexity = self.model(data)
                recon_loss = torch.mean((x_hat - data)**2) / self.dataset.train_var()
                loss = recon_loss + embedding_loss

                loss.backward()
                self.optimiser.step()

                self.total_losses.append(loss.item())

                if i % PRINT_AT == 0 :
                    print(f"Epoch: {epoch+1}/{self.epochs} Batch: {i+1}/{len(self.dataset.get_train())} Loss: {loss.item():.6f}")
        end = time.time()
        print(f"Total Time for training: {end - start:.2f}s")

    def validate(self) -> None :
        x, label = next(iter(self.dataset.get_test()))
        x = x.to(self.device)
        x = self.model.encoder(x)
        x = self.model.conv(x)
        _, x_hat, _, embeddings, _ = self.model.quantizer(x)
        x_recon = self.model.decoder(x_hat)

        rows = 4 
        batch = x_recon.shape[0]
        cols = batch // rows

        fig, axs = plt.subplots(rows, cols, figsize=(8, 4)) 
        axs = axs.ravel()

        for i in range(x_recon.shape[0]):
            axs[i].imshow(x_recon[i][0].detach().cpu(), cmap='gray')
            axs[i].axis('off')

        plt.subplots_adjust(wspace=0, hspace=0, left=0, right=1, bottom=0, top=1)
        plt.savefig(self.savepath + "/reconstructed.png")
            
                
    def plot(self, save = True) -> None :
        plt.figure(figsize=(10, 5))
        plt.plot(self.recon_loss, label='Reconstruction Loss')
        plt.plot(self.quant_loss, label='Quantisation Loss')
        plt.plot(self.total_losses, label='Total Loss')
        plt.title('Training Epochs against Loss for VQVAE')
        plt.xlabel('Iteration (Epoch * Batch Size)')
        plt.ylabel('Reconstruction Loss')
        plt.legend()
        plt.grid(True)

        if save :
            plt.savefig(self.savepath + '_train_loss.png')
        else :
            plt.show()

    def save(self, newpath = None) -> None :
        if newpath :
            torch.save(self.model.state_dict(), newpath)
        else :
            torch.save(self.model.state_dict(), self.savepath + '/vqvae.pth')

class TrainGAN(Trainer) :
    def __init__(self, model: nn.Module, dataset: Dataset, lr=1e-3, wd=0, epochs=10, savepath='./models/gan') :
        super().__init__(model, dataset, lr, wd, epochs, savepath)

        self.d_optim = torch.optim.Adam(self.model.discriminator.parameters(), lr = self.lr)
        self.g_optim = torch.optim.Adam(self.model.generator.parameters(), lr = self.lr)
        # self.criterion = nn.BCEWithLogitsLoss().to(DEVICE)        
        self.criterion = nn.BCELoss().to(DEVICE)
        self.d_losses = list()
        self.g_losses = list()
        self.latent = NOISE

    def train(self) -> None :
        if self.dataset.train_unloaded() :
            self.dataset.load_train()
        
        self.model.discriminator.train()
        self.model.generator.train()

        start = time.time()
        for epoch in range(self.epochs) :
            for i, (data, label) in enumerate(self.dataset.get_train()) :
                data = data.to(DEVICE)
                self.model.discriminator.zero_grad()

                noise = torch.randn(data.shape[0], self.latent, 1, 1).to(DEVICE)
                fake = self.model.generator(noise)
                
                real_pred = self.model.discriminator(data)
                fake_pred = self.model.discriminator(fake)

                real_loss = self.criterion(real_pred, torch.ones_like(real_pred))
                fake_loss = self.criterion(fake_pred, torch.zeros_like(fake_pred))

                d_loss = real_loss + fake_loss
                d_loss.backward()
                self.d_optim.step()

                self.model.generator.zero_grad()
                # Recreate the fake data after updating the discriminator
                noise = torch.randn(data.shape[0], self.latent, 1, 1).to(DEVICE)
                fake = self.model.generator(noise)

                output = self.model.discriminator(fake).reshape(-1)
                g_loss = self.criterion(output, torch.ones_like(output))
                g_loss.backward()
                self.g_optim.step()

                if (i % PRINT_AT == 0):
                    print(f"Epoch: {epoch+1}/{self.epochs} Batch: {i+1}/{len(self.dataset.get_train())} Loss D: {d_loss.item():.6f}, Loss G: {g_loss.item():.6f}")
            
                self.g_losses.append(d_loss.item())
                self.d_losses.append(g_loss.item())  
        end = time.time()
        print(f"Total Time for training: {end - start:.2f}s")

    def validate(self) -> None :
        pass
                
    def plot(self, save = True, show = True) -> None :
        plt.figure(figsize=(10, 5))
        plt.plot(self.d_losses, label='Discriminator Loss')
        plt.plot(self.g_losses, label='Generator Loss')
        plt.xlabel('Iteration (Batch * Epoch)')
        plt.ylabel('BCE Loss')
        plt.legend()
        plt.grid(True)
        plt.title('GAN Training Loss')
        if save :
            plt.savefig(self.savepath + '_train_loss.png')
        if show :
            plt.show()
    
    def save(self, discriminator_path = None, generator_path = None) -> None :
        if discriminator_path and generator_path :
            torch.save(self.model.generator.state_dict(), generator_path)
            torch.save(self.model.discriminator.state_dict(), discriminator_path)
        else :
            torch.save(self.model.generator.state_dict(), self.savepath + '/discriminator.pth')
            torch.save(self.model.discriminator.state_dict(), self.savepath + '/generator.pth')