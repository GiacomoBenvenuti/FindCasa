import os
import json
import pandas as pd


def features_extraction(folder_path:str = "data/"):
    """Extract features from JSON files in the specified folder.

    :param str folder_path: The path to the folder containing JSON files, defaults to "data/"
    """
    # Initialize an empty list to store rows for the DataFrame
    data_rows = []

    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
        # Check if the file name starts with "id" and ends with ".json"
        if filename.startswith("id") and filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)

            # Open and read the JSON file
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    
                    # Extract the required fields based on working_fields
                    row = {}
                    row["id"] = data["propertyData"]["id"]  # Get value for field, default to None if not found
                    row["price"] = data["propertyData"]["prices"]["primaryPrice"]
                    row["latitude"] = data["propertyData"]["location"]["latitude"]
                    row["longitude"] = data["propertyData"]["location"]["longitude"]
                    row["address"] = data["propertyData"]["address"]["displayAddress"]
                    row["published"] = data["propertyData"]["status"]["published"]
                    row["archived"] = data["propertyData"]["status"]["archived"]
                    row["date"] = data["propertyData"]["listingHistory"]["listingUpdateReason"]
                    row["tenure"] = data["propertyData"]["tenure"]["tenureType"]
                    row["ownership"] = data["analyticsInfo"]["analyticsProperty"]["ownership"]
                    row["postcode"] = data["analyticsInfo"]["analyticsProperty"]["postcode"]
                    row["preOwned"] = data["analyticsInfo"]["analyticsProperty"]["preOwned"]
                    row["propertySubType"] = data["analyticsInfo"]["analyticsProperty"]["propertySubType"]
                    row["ppropertyType"] = data["analyticsInfo"]["analyticsProperty"]["propertyType"]
                    row["bedrooms"] = data["propertyData"]["bedrooms"]
                    row["bathooms"] = data["propertyData"]["bathrooms"]
                    row["price_sqm"] = data["propertyData"]["prices"]["pricePerSqFt"]
                    # row["EPC"] = data["propertyData"]["epcGraphs"]["pricePerSqFt"]
                    row["tax"] = data["propertyData"]["livingCosts"]["councilTaxBand"]

        
                    for i in range(4):
                    
                        if data["propertyData"]["sizings"][i]["unit"] == "sqm":
                            row["size_sqm"] = data["propertyData"]["sizings"][i]["maximumSize"]
                        
                        if data["propertyData"]["sizings"][i]["unit"] == "sqft":
                            row["size_sqf"] = data["propertyData"]["sizings"][i]["maximumSize"]
                    

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
    df.to_csv("properties.csv")

if __name__=="__main__":
    features_extraction()