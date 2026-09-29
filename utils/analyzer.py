def analyze_dataset(data, selected_column=None):
    charts = {}
    if data is None or data.empty:
        return charts

    numeric = data.select_dtypes(include=['number']).columns.tolist()
    categorical = data.select_dtypes(include=['object', 'category']).columns.tolist()

    if categorical:
        category = categorical[0]
        counts = data[category].fillna("Missing").value_counts().head(6)
        charts["bar1"] = {
            "title": f"Top {category} Categories",
            "description": f"This chart shows the most frequent values for {category}.",
            "labels": counts.index.astype(str).tolist(),
            "values": counts.values.tolist(),
        }
    elif numeric:
        metric = numeric[0]
        sample = data[metric].dropna().head(6)
        charts["bar1"] = {
            "title": f"Sample {metric} Values",
            "description": f"This chart shows a sample of {metric} values from the dataset.",
            "labels": [f"Row {i+1}" for i in range(len(sample))],
            "values": sample.tolist(),
        }

    chart_column = selected_column if selected_column in numeric else (numeric[0] if numeric else None)
    if chart_column:
        series = data[chart_column].dropna().head(10)
        charts["bar2"] = {
            "title": f"{chart_column} Trend Preview",
            "description": f"This chart shows the first values of {chart_column} after cleanup.",
            "labels": [f"Row {i+1}" for i in range(len(series))],
            "values": series.tolist(),
        }

    return charts
