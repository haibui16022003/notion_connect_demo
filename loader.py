import json
import csv
import notion_client
import os
import logging
import requests

from test import has_more, page_ids, response
from util.config import Config


conf = Config('config.ini')


def read_json(file_name) -> list:
    with open(file_name, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return [data]
        except json.JSONDecodeError:
            f.seek(0)
            return [json.loads(line) for line in f if line.strip()]


class Loader:
    def __init__(self, list_files: []):
        self.list_files = [file for file in list_files if os.path.exists(file)]
        if not self.list_files:
            raise ValueError("No valid files found!")

        self.notion_connector = conf.get_section_conf('notion')
        self.notion_client = notion_client.Client(auth=self.notion_connector["api_key"])
        self.notion_id = self.notion_connector["notion_id"]
        self.tag_mapping = ['category', 'light_type', 'water_type', 'earth_type', 'humidity_type', 'fertilizer_type', 'breeding_type']
        self.tag_data = self.read_tag()

    def read_tag(self) -> dict:
        tag_data = {}
        for tag_type in self.tag_mapping:
            tag_data[tag_type] = {}
            file_name = './data/' + tag_type + '.csv'
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    csv_reader = csv.DictReader(f)
                    data = [row for row in csv_reader]
                    tag_data[tag_type] = data
            except UnicodeDecodeError as e:
                logging.error(f"Error reading {file_name}: {e}")
        # print(tag_data)
        return tag_data

    def process_tag(self, tag_ids, tag_type):
        return [
            {"name": tag[" tag_name"].strip()}
            for tag_id in tag_ids
            for tag in self.tag_data[tag_type]
            if str(tag["id"]) == str(tag_id)
        ] or [{"name": "Unknown"}]

    def process_single_tag(self, tag_id, tag_type):
        for tag in self.tag_data[tag_type]:
            if str(tag["id"]) == str(tag_id):
                return {"name": tag[" tag_name"].strip()}
        return {"name": "Unknown"}

    def import_to_notion_single(self, data_file):
        data = read_json(data_file)
        for line in data:
            self.upload(line)

    def import_to_notion_multi(self):
        for data_file in self.list_files:
            self.import_to_notion_single(data_file)

    def upload(self, json_line):
        is_available = json_line["quantity"] > 0
        print(json_line)
        notion_page = {
            "Tên": {"title": [{"text": {"content": json_line["name"]}}]},
            "Giá": {"number": json_line["price"]},
            "Đặc điểm": {"rich_text": [{"text": {"content": json_line["feature"]}}]},
            "Nhóm cây": {"select": self.process_single_tag(json_line["category"], "category")},
            "Ánh sáng": {"multi_select": self.process_tag(json_line["light_type"], "light_type")},
            "Nước": {"multi_select": self.process_tag(json_line["water_type"], "water_type")},
            "Đất": {"multi_select": self.process_tag(json_line["earth_type"], "earth_type")},
            "Độ ẩm": {"multi_select": self.process_tag(json_line["humidity_type"], "humidity_type")},
            "Phân bón": {"multi_select": self.process_tag(json_line["fertilizer_type"], "fertilizer_type")},
            "Nhân giống": {"multi_select": self.process_tag(json_line["breeding_type"], "breeding_type")},
            "Ghi chú": {"rich_text": [{"text": {"content": json_line["note"]}}]},
            "Còn hàng": {"checkbox": is_available}
        }

        print(notion_page)

        image_block = None
        if "image_url" in json_line and json_line["image_url"]:
            image_block = {
                "object": "block",
                "type": "image",
                "image": {"type": "external", "external": {"url": json_line["image_url"]}}
            }

        try:
            self.notion_client.pages.create(
                parent={"database_id": self.notion_id},
                properties=notion_page,
                children=[image_block] if image_block else []
            )
        except Exception as e:
            logging.error(f"Error uploading to Notion: {e}")
            print(f"Error: {e}")

    def clear(self):
        url = f"https://api.notion.com/v1/databases/{self.notion_id}/query"
        headers = {
            "Authorization": f"Bearer {self.notion_connector["api_key"]}",
            "Notion-Version": "2022-06-28"
        }

        has_more = True
        next_page = None
        page_ids = []

        while has_more:
            payload = {"start_page": next_page} if next_page else {}
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()

            page_ids.extend([page["id"] for page in data.get("results", [])])
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor", None)

        for page_id in page_ids:
            try:
                delete_url = f"https://api.notion.com/v1/pages/{page_id}"
                requests.patch(delete_url, headers=headers, json={"archived": True})
                logging.info(f"Page {page_id} deleted")
            except Exception as e:
                logging.error(f"Error archiving page {page_id}: {e}")


    def load(self):
        self.clear()
        if len(self.list_files) == 1:
            self.import_to_notion_single(self.list_files[0])
        else:
            self.import_to_notion_multi()
