import pandas as pd
import os

def extract_text(path_to_parquet="../../data/raw/", remove_old=False):
    """
    Сохраняет только тексты документов из оригинальных .parquet файлов в новые.
    :param path_to_parquet: Путь к папке, где лежат .parquet файлы документов.
    :param remove_old: Если True, удаляет изначальные .parquet файлы.
    :return: None
    """
    n_files = len(os.listdir(path_to_parquet))
    print(f"0 / {n_files}")

    for i in range(n_files):
        print(f"{i + 1} / {n_files}")
        file_path = os.path.join(path_to_parquet, "{:04d}.parquet".format(i))

        df = pd.read_parquet(file_path)
        df[["textIPS"]].to_parquet(os.path.join(path_to_parquet, "text{}.parquet".format(i)))

        if remove_old:
            os.remove(file_path)

if __name__ == "__main__":
    extract_text()
