import requests
import json

url = "https://openweb.nlb.gov.sg/api/v1/EResource/SearchResources"

# Corrected headers with proper Content-Type
headers = {
    "X-API-Key": "QAL;<!`w+0]=DF]HxrNTZ>X`{Hf9m=Qa",  # Replace with your actual API key
    "X-App-Code": "DEV-ChunOwen"
}

# Add at least one required field such as Title, Creator, or ISBN
params = {
    "Subject": "Humor (Nonfiction)",
    "ContentType": "eBooks",
    "Limit" : 100
}

# Send the GET request with headers and query parameters
response = requests.get(url, headers=headers, params=params)

# Check if the request was successful
if response.status_code == 200:
    print("Success!")

    # Convert the JSON response to a dictionary
    response_data = response.json()

    # Save the response to a file
    with open('nlb_api_response.json', 'w') as file:
        json.dump(response_data, file, indent=4)  # Save with pretty-printing (indent=4)

    print("Response saved to nlb_api_response.json")
else:
    print(f"Error {response.status_code}: {response.text}")
