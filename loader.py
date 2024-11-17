import json
import csv
import notion_client
import os
import logging

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
        self.tag_mapping = ['light_type', 'water_type', 'earth_type', 'humidity_type', 'fertilizer_type', 'breeding_type']
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
        return tag_data

    def process_tag(self, tag_ids, tag_type):
        return [{"name": self.tag_data[tag_type][0].get(tag_id, "Unknown")} for tag_id in tag_ids]

    def import_to_notion_single(self, data_file):
        data = read_json(data_file)
        for line in data:
            self.upload(line)

    def import_to_notion_multi(self):
        for data_file in self.list_files:
            self.import_to_notion_single(data_file)

    def upload(self, json_line):
        is_available = json_line["quantity"] > 0

        notion_page = {
            "Tên": {"title": [{"text": {"content": json_line["name"]}}]},
            "Giá": {"number": json_line["price"]},
            "Đặc điểm": {"rich_text": [{"text": {"content": json_line["feature"]}}]},
            "Nhóm cây": {"select": {"name": str(json_line["category"])}},
            "Ánh sáng": {"multi_select": self.process_tag(json_line["light_type"], "light_type")},
            "Nước": {"multi_select": self.process_tag(json_line["water_type"], "water_type")},
            "Đất": {"multi_select": self.process_tag(json_line["earth_type"], "earth_type")},
            # "Độ ẩm": {"select": {"name": self.process_tag(json_line["humidity_type"], "humidity_type")},},
            "Phân bón": {"multi_select": self.process_tag(json_line["fertilizer_type"], "fertilizer_type")},
            "Nhân giống": {"multi_select": self.process_tag(json_line["breeding_type"], "breeding_type")},
            "Ghi chú": {"rich_text": [{"text": {"content": json_line["note"]}}]},
            "Còn hàng": {"checkbox": is_available}
        }

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

    def load(self):
        if len(self.list_files) == 1:
            self.import_to_notion_single(self.list_files[0])
        else:
            self.import_to_notion_multi()
