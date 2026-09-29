from sklearn.linear_model import LinearRegression
import numpy as np


def train_model(data, sold_column):

    data['day'] = range(1, len(data)+1)

    X = data[['day']]
    y = data[sold_column]

    model = LinearRegression()

    model.fit(X, y)

    prediction = model.predict([[len(data)+1]])

    return model, prediction[0]