from utils import *
import numpy as np
from torchvision import transforms
from PIL import Image


def stegano_solver(cover_im: np.ndarray, message: str) -> str:
    pass


image = Image.open("H:\HackTrick24\SteganoGAN\encoded.png")

# Convert the image to a tensor
to_tensor = transforms.ToTensor()
image_tensor = to_tensor(image)

# Add a batch dimension
image_tensor = image_tensor.unsqueeze(0)

# Decode the image tensor
decoded_text = decode(image_tensor)

# Now you have the decoded text
print(decoded_text)
