import pandas as pd


def rename_cols(df: pd.DataFrame, rename_map: dict):
    corrected_map = {}
    for col, new in rename_map.items():
        candidate_cols = [c for c in df if col in c]
        if len(candidate_cols) > 1:
            raise ValueError(f"Multiple matches for column: {col}")
        corrected_map[candidate_cols[0]] = new
    return df.rename(columns=corrected_map)
