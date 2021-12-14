import torch
import torch.nn as nn

class SimSiam(nn.Module):
    """
    Build a SimSiam model.
    """
    def __init__(self, base_encoder, dim=2048, pred_dim=512, stop_grad=True, include_predictor=True):
        """
        dim: feature dimension (default: 2048)
        pred_dim: hidden dimension of the predictor (default: 512)
        """
        super(SimSiam, self).__init__()
        
        self.stop_grad = stop_grad
        self.include_predictor = include_predictor

        # create the encoder
        # num_classes is the output fc dimension, zero-initialize last BNs
        self.encoder = base_encoder

        # build a 3-layer projector
        prev_dim = self.encoder.fc.weight.shape[1]
        self.encoder.fc = nn.Sequential(nn.Linear(prev_dim, dim, bias=False),
                                        nn.BatchNorm1d(dim),
                                        nn.ReLU(inplace=True), # first layer
                                        nn.Linear(dim, dim, bias=False),
                                        nn.BatchNorm1d(dim, affine=False)) # output layer
        #self.encoder.fc[3].bias.requires_grad = False # hack: not use bias as it is followed by BN

        # build a 2-layer predictor
        if self.include_predictor:
            self.predictor = nn.Sequential(nn.Linear(dim, pred_dim, bias=False),
                                            nn.BatchNorm1d(pred_dim),
                                            nn.ReLU(inplace=True), # hidden layer
                                            nn.Linear(pred_dim, dim)) # output layer
        else:
            self.predictor = Identity()

    def forward(self, x1, x2):
        """
        Input:
            x1: first views of images
            x2: second views of images
        Output:
            p1, p2, z1, z2: predictors and targets of the network
            See Sec. 3 of https://arxiv.org/abs/2011.10566 for detailed notations
        """

        # compute features for one view
        z1 = self.encoder(x1) # NxC
        z2 = self.encoder(x2) # NxC

        p1 = self.predictor(z1) # NxC
        p2 = self.predictor(z2) # NxC
        
        if self.stop_grad:
            z1, z2 = z1.detach(), z2.detach()

        return p1, p2, z1, z2
    
    def forward_lat(self, x):
        x = self.encoder(x)
        return self.predictor(x)
    
    def forward_lat_pool(self, x):
        enc_temp = self.encoder
        enc_temp.fc = Identity()
        x = enc_temp(x)
        return x

class Identity(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x):
        return x
