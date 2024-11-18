# import notion_client
#
# notion_client = notion_client.Client(auth="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")
#
# def fetch_database_schema(database_id):
#     try:
#         database = notion_client.databases.retrieve(database_id=database_id)
#         print("Properties in the database:")
#         for prop, details in database["properties"].items():
#             print(f"{prop} - {details['type']}")
#     except Exception as e:
#         print(f"Error fetching schema: {e}")
#
# database_id = "141c01c87bec80ec9415cf5379f34ab2"
# fetch_database_schema(database_id)

import requests

header = {
    "Authorization": "Bearer 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",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/141c01c87bec80ec9415cf5379f34ab2/query"
has_more = True
next_cursor = None
page_ids = []

while has_more:
    payload = {"start_cursor": next_cursor} if next_cursor else {}
    response = requests.post(url, headers=header, data=payload)

    response.raise_for_status()
    data = response.json()
    page_ids.extend([page["id"] for page in data.get("results", [])])
    has_more = data.get("has_more", False)
    next_cursor = data.get("next_cursor", None)

print(page_ids)

for page_id in page_ids:
        try:
            delete_url = f"https://api.notion.com/v1/pages/{page_id}"
            requests.patch(delete_url, headers=header, json={"archived": True})
        except Exception as e:
            print(e)