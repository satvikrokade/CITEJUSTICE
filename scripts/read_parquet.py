import pandas as pd

df = pd.read_parquet("metadata.parquet")

with pd.ExcelWriter("Indian_Supreme_Court_Metadata.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="All Cases", index=False)

    summary = pd.DataFrame({
        "Column": df.columns,
        "Datatype": [str(x) for x in df.dtypes],
        "Null Values": df.isnull().sum().values,
        "Unique Values": df.nunique().values
    })

    summary.to_excel(writer, sheet_name="Column Summary", index=False)

print("Excel file created successfully.")