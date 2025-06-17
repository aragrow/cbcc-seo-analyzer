def process_sheet(sheet_data: dict, stage: str) -> dict:
    
    global debug
    debug += f"Executing -> process_sheet()\n"
        
    results = []
    message = []
    if sheet_data is None:
        debug += "No sheet data provided\n"
        raise

    if not isinstance(sheet_data, dict):
        debug += "Sheet data is not a dictionary.\n"
        raise

    debug += f"Processing {len(sheet_data)} sheets.\n"

    for sheet_name, df in sheet_data.items():
        if not isinstance(df, pd.DataFrame):
            results.append(f"<li><strong>{sheet_name}</strong>: Failed to load tab (not a DataFrame)</li>")
            continue
        row_count = len(df)
        col_count = len(df.columns)
        message.append(f"<li><strong>{sheet_name}</strong>: {row_count} rows, {col_count} columns</li>")
        if sheet_name == "Site Speed & Asset Optimization":
            results.append({"siteSpeedAssetOptimization": load_site_speed_asset_optimization(df)})


    return results
# End process_sheet