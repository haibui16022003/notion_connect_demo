import requests
from util.config import Config

def get_database(database_id, notion_token):
    url = f"https://api.notion.com/v1/databases/{database_id}"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # Ensure you're specifying the correct API version.
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {
                "status": "error",
                "code": response.status_code,
                "message": response.text
            }
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

# Retrieve configuration
conf = Config(config_file="config.ini")
get_config = conf.get_section_conf("notion")
database_id = get_config.get("notion_id")
notion_token = get_config.get("api_key")

# Test the connection
database_info = get_database(database_id, notion_token)

if database_info["status"] == "success":
    print("Connection successful!")
    print(database_info["data"])
else:
    print(f"Connection failed: {database_info['code']}")
    print(database_info["message"])
