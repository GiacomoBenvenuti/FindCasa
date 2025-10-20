import os
import json
import pandas as pd

from config_loader import get_config


def features_extraction(folder_path: str = None):
    """Extract features from JSON files in the specified folder.

    :param str folder_path: The path to the folder containing JSON files.
                           If None, uses default from config.
    """
    # Load configuration
    config = get_config()
    
    # Use folder path from config if not provided
    if folder_path is None:
        folder_path = config.get('feature_extraction.input_directory', 'data/')
    
    # Get file filtering settings from config
    file_prefix = config.get('feature_extraction.file_filter.prefix', 'id')
    file_suffix = config.get('feature_extraction.file_filter.suffix', '.json')
    
    # Get CSV output settings
    csv_filename = config.get('feature_extraction.csv_output.filename',
                              'properties.csv')
    include_index = config.get('feature_extraction.csv_output.include_index',
                               False)
    
    # Initialize an empty list to store rows for the DataFrame
    data_rows = []

    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
        # Check if the file name starts with prefix and ends with suffix
        if filename.startswith(file_prefix) and filename.endswith(file_suffix):
            file_path = os.path.join(folder_path, filename)

            # Open and read the JSON file
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    
                    # Extract the required fields
                    row = {}
                    # Get property data fields
                    prop_data = data["propertyData"]
                    analytics_data = data["analyticsInfo"]["analyticsProperty"]
                    
                    row["id"] = prop_data["id"]
                    row["price"] = prop_data["prices"]["primaryPrice"]
                    row["latitude"] = prop_data["location"]["latitude"]
                    row["longitude"] = prop_data["location"]["longitude"]
                    row["address"] = prop_data["address"]["displayAddress"]
                    row["published"] = prop_data["status"]["published"]
                    row["archived"] = prop_data["status"]["archived"]
                    row["date"] = prop_data["listingHistory"][
                        "listingUpdateReason"]
                    row["tenure"] = prop_data["tenure"]["tenureType"]
                    row["ownership"] = analytics_data["ownership"]
                    row["postcode"] = analytics_data["postcode"]
                    row["preOwned"] = analytics_data["preOwned"]
                    row["propertySubType"] = analytics_data["propertySubType"]
                    row["ppropertyType"] = analytics_data["propertyType"]
                    row["bedrooms"] = prop_data["bedrooms"]
                    row["bathooms"] = prop_data["bathrooms"]
                    row["price_sqm"] = prop_data["prices"]["pricePerSqFt"]
                    row["tax"] = prop_data["livingCosts"]["councilTaxBand"]

                    for i in range(4):
                        sizing = prop_data["sizings"][i]
                        if sizing["unit"] == "sqm":
                            row["size_sqm"] = sizing["maximumSize"]
                        
                        if sizing["unit"] == "sqft":
                            row["size_sqf"] = sizing["maximumSize"]
                    

                    # Append the row to the data list
                    data_rows.append(row)

                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file: {filename}")
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")

    # Create a Pandas DataFrame from the extracted data
    df = pd.DataFrame(data_rows)

    # Display the DataFrame
    print(df)
    df.to_csv(csv_filename, index=include_index)

if __name__=="__main__":
    features_extraction()