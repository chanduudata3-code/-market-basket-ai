def generate_suggestions(data):
    if data is None or data.empty:
        return ["No data available to generate suggestions."]

    suggestions = []
    categorical = data.select_dtypes(include=['object', 'category']).columns.tolist()
    numeric = data.select_dtypes(include=['number']).columns.tolist()

    if categorical:
        category = categorical[0]
        top_value = data[category].fillna("Missing").mode()
        if not top_value.empty:
            suggestions.append(
                f"The most frequent value in '{category}' is '{top_value.iloc[0]}'. Use this insight to prioritize common segments."
            )

    if numeric:
        primary = numeric[0]
        average = data[primary].mean()
        suggestions.append(
            f"The average value for {primary} is {round(average, 2)}. Use this threshold to identify underperforming rows."
        )

    if len(numeric) >= 2:
        x = numeric[0]
        y = numeric[1]
        correlation = data[x].corr(data[y])
        if correlation is not None:
            if correlation > 0.5:
                suggestions.append(
                    f"{x} and {y} are positively correlated. Improving {x} may help raise {y}."
                )
            elif correlation < -0.5:
                suggestions.append(
                    f"There is a negative relationship between {x} and {y}. A trade-off may exist between these values."
                )

    if not suggestions:
        suggestions.append(
            "Add more numeric or categorical columns for richer insights and predictions."
        )

    suggestions.append(
        "Review the dataset for missing values and anomalies to improve future predictions."
    )

    return suggestions
