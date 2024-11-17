import os
from loader import Loader


def main():
    data_files = [
        os.path.join("data","data.json"),
        os.path.join("data", "data1.json"),
        os.path.join("data", "data2.json"),
    ]

    del_list = []
    for idx, data_file in enumerate(data_files):
        if not os.path.exists(data_file):
            # data_files.remove(data_file)
            print(f"{data_file} not found")
            del_list.append(idx)

    del_list.reverse()
    for i in del_list:
        del data_files[i]

    print(data_files)

    if data_files:
        loader = Loader(data_files)
        loader.load()

if __name__ == '__main__':
    main()