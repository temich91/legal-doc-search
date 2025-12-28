import os
import pandas as pd
import numpy as np
import faiss
from src.embedder.rulaw_embedder import RuLawEmbedder
import warnings

warnings.filterwarnings(
    "ignore",
    message="Some weights of the model checkpoint.*"
)

def create_faiss_index(parquet_path="../data/processed", index_path="../tmp"):
    all_embeddings = []
    metadata = []
    for file in os.listdir(parquet_path):
        df = pd.read_parquet(os.path.join(parquet_path, file))
        embeddings = np.stack(df["embedding"].values)
        all_embeddings.append(embeddings)

        for i in range(len(embeddings)):
            metadata.append({"file": file, "index": i})

    all_embeddings = np.vstack(all_embeddings)
    d = all_embeddings.shape[1]

    index = faiss.IndexFlatL2(d)
    index.add(all_embeddings.astype("float32"))

    return index, metadata

def search_nearest(query_embedding, index, metadata, k=5):
    query = np.array(query_embedding).astype('float32').reshape(1, -1)
    distances, indices = index.search(query, k)
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({**metadata[idx], 'distance': distances[0][i]})

    return results


if __name__ == "__main__":
    embedder = RuLawEmbedder("model/")
    index, metadata = create_faiss_index("../data/processed_txt")

    query = input("Введите запрос:")
    query_embedding = embedder.get_embedding(query)

    results = search_nearest(query_embedding, index, metadata, k=10)
    i = 1
    print(results[-1])

    # for res in results:
    #     text_num = res["file"][4]
    #     text_df = pd.read_parquet(f"../data/raw/text{text_num}.parquet")
    #     index = res['index']
    #     print(f"{i}) {text_df.iloc[index].item()}, Схожесть: {res['distance']:.2f}")
    #     print()
    #     i += 1
