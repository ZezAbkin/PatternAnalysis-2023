import torch
import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F

class RawSiameseModel(nn.Module):
    def __init__(self):
        super(RawSiameseModel, self).__init__()
        # Follow https://www.cs.cmu.edu/~rsalakhu/papers/oneshot1.pdf -> Siamese Neural Networks for One-shot Image Recognition
        # first convolution layer
        self.model1 = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=64, kernel_size=10, stride=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2)
        )

        self.model2 = nn.Sequential(
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=7, stride=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2)
        )

        self.model3 = nn.Sequential(
            nn.Conv2d(in_channels=128, out_channels=128, kernel_size=4, stride=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2)
        )

        self.model4 = nn.Sequential(
            nn.Conv2d(in_channels=128, out_channels=256, kernel_size=4, stride=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(256 * 6 * 6, 4096),
        )

    def forward(self, x):
        output = self.model1(x)
        output = self.model2(output)
        output = self.model3(output)
        output = self.model4(output)

        return output

class BinaryModelClassifier(nn.Module):

    def __init__(self):
        # Reference: https://machinelearningmastery.com/building-a-binary-classification-model-in-pytorch/
        super(BinaryModelClassifier, self).__init__()

        # dummy linear layer
        self.binary_layer = nn.Sequential(
            nn.Linear(4096, 1024),
            nn.ReLU(),
            nn.Linear(1024, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        output = self.binary_layer(x)
        return output

class ContrastiveLossFunction(nn.Module):
    # custom loss function based on https://www.kaggle.com/code/robinreni/signature-classification-using-siamese-pytorch
    def __init__(self):
        super(ContrastiveLossFunction, self).__init__()
        self.margin = 0.5

    def forward(self, output1, output2, label): 
        output = F.pairwise_distance(output1, output2)
        loss_contrastive = torch.mean((1-label) * torch.pow(output, 2) + (label) * torch.pow(torch.clamp(self.margin - output, min=0.0), 2))

        return loss_contrastive