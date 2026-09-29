import numpy as np


def generate_summary(prediction):
    if not prediction or not prediction.get("actual"):
        return ["Not enough data to generate a prediction summary."]

    actual = np.array(prediction["actual"], dtype=float)
    predicted = np.array(prediction.get("predicted", []), dtype=float)
    summary = []

    if len(actual) > 1:
        slope = (actual[-1] - actual[0]) / max(len(actual) - 1, 1)
        if slope > 0.5:
            summary.append("The historical data shows a rising trend.")
        elif slope < -0.5:
            summary.append("The historical data shows a downward trend.")
        else:
            summary.append("The historical data is relatively stable.")
    else:
        summary.append("There is too little history to determine a strong trend.")

    std_dev = float(np.std(actual))
    summary.append(
        "The dataset shows moderate variability." if std_dev <= 2 else "The dataset shows notable fluctuations."
    )

    if predicted.size >= 2:
        change = predicted[-1] - predicted[0]
        if abs(change) < 1:
            summary.append("Future values are projected to remain stable.")
        elif change > 0:
            summary.append("Future values are projected to rise.")
        else:
            summary.append("Future values are projected to decline.")
    else:
        summary.append("Prediction data is limited, so future performance is tentative.")

    summary.append(
        "Watch for missing or irregular values, as they have been handled automatically for this model."
    )

    return summary