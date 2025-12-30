import uuid
from src.embedder.rulaw_embedder import RuLawEmbedder
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from parser import Parser
from chunker import Chunker
from tqdm import tqdm
import time
import random
from src.paths import SRC_DIR

COLLECTION_NAME = "legal_fabulas"
EDGE_DRIVER_PATH = SRC_DIR / "parser" / "msedgedriver.exe"
MODEL_PATH = SRC_DIR / "model"
EMBEDDING_MODEL = RuLawEmbedder(MODEL_PATH)
COLLECTION_BATCH_SIZE = 64

def main():
    """
    Парсит ссылки на документы и их текст.
    """

    chunker = Chunker()

    model = EMBEDDING_MODEL
    embedding_dim = model.model.get_input_embeddings().embedding_dim

    client = QdrantClient(host="localhost", port=6333, timeout=60)
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE
            )
        )
    print("коллекция qdrant создана")

    batch = []
    try:
        with Parser(EDGE_DRIVER_PATH) as parser:
            # Сбор ссылок со страницы поиска
            links_page = parser.get_links_list_page("https://sudrf.cntd.ru/search?type=777720157&startDate=2021-01-01&endDate=2025-12-01", max_scroll=2)
            links = parser.get_docs_links(links_page)
        print(f"Загружается {len(links)} ссылок")

        for idx in tqdm(range(len(links)), desc="Обработано ссылок"):
            link = links[idx]
            paragraphs = chunker.get_paragraphs(link, without_title=True) # 1 request
            chunks = chunker.chunk_paragraphs(paragraphs)
            if not chunks:
                continue
            time.sleep(random.uniform(1.0, 2.0))

            embeddings = model.get_embedding(
                chunks,
                batch_size=32,
            )

            for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
                batch.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector.tolist(),
                        payload={
                            "link": link,
                            "text": chunk
                        }
                    )
                )

                if len(batch) >= COLLECTION_BATCH_SIZE:
                    client.upsert(
                        collection_name=COLLECTION_NAME,
                        points=batch
                    )
                    batch.clear()
                    print(f"{COLLECTION_BATCH_SIZE} точек записано")
        if batch:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch
            )

    except Exception as e:
        print(e)
        time.sleep(10)

if __name__ == "__main__":
    main()
