def quality_report(df):
    return {
        "shape": df.shape,
        "missing_values": df.isna().sum().to_dict(),
        "duplicates": df.duplicated().sum(),
        "dtypes": df.dtypes.astype(str).to_dict()
    }

if __name__ == "__main__":
    from transform import transform
    df = transform()
    print(quality_report(df))
