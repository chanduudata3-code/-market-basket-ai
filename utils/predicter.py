import numpy as np
from sklearn.linear_model import LinearRegression


def predict_trend(data, selected_column=None):
    if data is None or data.empty:
        return None

    numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
    column = selected_column if selected_column in numeric_cols else (numeric_cols[0] if numeric_cols else None)
    if not column:
        return None

    series = data[column].astype(float).dropna()
    if len(series) < 3:
        return None

    values = series.values
    X = np.arange(len(values)).reshape(-1, 1)

    try:
        model = LinearRegression()
        model.fit(X, values)
        future_X = np.arange(len(values), len(values) + 5).reshape(-1, 1)
        prediction = model.predict(future_X)
        return {
            "column": column,
            "actual": values.tolist(),
            "predicted": np.round(prediction, 2).tolist(),
        }
    except Exception:
        return None
