import numpy as np
data = np.array([[25.5, 26.0, 28.5], [29.1, 30.2, 27.8]])
data.shape
data.mean(axis=1)
data[data > 28.0]
normalized = (data - data.min()) / (data.max() - data.min())
np.round(normalized, 2)