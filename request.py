import requests
import json
from categories import categories
import time

url = "https://openweb.nlb.gov.sg/api/v1/EResource/SearchResources"

headers = {
    "X-API-Key": "QAL;<!`w+0]=DF]HxrNTZ>X`{Hf9m=Qa",
    "X-App-Code": "DEV-ChunOwen"
}

for i, items in enumerate(categories):

    params = {
        "Subject": f"{items}",
        "ContentType": "eBooks",
        "Limit" : 100
    }

    time.sleep(10)

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        print("Success!")

        response_data = response.json()

        with open(f'nlb_api_response{i}.json', 'w') as file:
            json.dump(response_data, file, indent=4)

        print(f"Response saved to nlb_api_response{i}.json")
    else:
        print(f"Error {response.status_code}: {response.text}")
