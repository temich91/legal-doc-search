from multiprocessing import Pool
import uuid
from src.embedder.rulaw_embedder import RuLawEmbedder
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from src.parser.test import Parser
from chunker import Chunker
from tqdm import tqdm
import time
import random
from src.paths import SRC_DIR

SEARCH_PAGE_LINK = "https://sudrf.cntd.ru/search?type=777720157&startDate=2021-01-01&endDate=2025-12-01"
COLLECTION_NAME = "legal_fabulas_test"
EDGE_DRIVER_PATH = SRC_DIR / "parser" / "msedgedriver.exe"
MODEL_PATH = SRC_DIR / "model"
COLLECTION_BATCH_SIZE = 64
EMBEDDING_DIM = 768

model = None

def init_worker():
    global model, chunker
    model = RuLawEmbedder(MODEL_PATH)
    chunker = Chunker()
    print("worker init done")

def embed(chunks):
    global model
    if not chunks:
        return []

    link, chunks = chunks
    embeddings = model.get_embedding(
        chunks,
        batch_size=32,
    )
    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector.tolist(),
                payload={
                    "link": link,
                    "text": chunk
                }
            )
        )

    return points

def main():
    """
    Парсит ссылки на документы и их текст.
    """

    client = QdrantClient(host="localhost", port=6333, timeout=60)
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE
            )
        )
    print("коллекция qdrant создана")

    all_points = []
    try:
        chunker = Chunker()
        with Parser(EDGE_DRIVER_PATH) as parser:
            # Сбор ссылок со страницы поиска
            links = parser.get_docs_links(SEARCH_PAGE_LINK, max_scroll=15) # заменить на parser.parse_all()
        print(f"Загружается {len(links)} ссылок")
        chunks = []
        for link in links:
            paragraphs = chunker.get_paragraphs(link, without_title=True)  # 1 request
            chunks.append((link, chunker.chunk_paragraphs(paragraphs)))

        with Pool(processes=4, initializer=init_worker) as pool:
        # with Pool(processes=cpu_count() - 1, initializer=init_worker) as pool:
            for pts in tqdm(pool.imap_unordered(embed, chunks), total=len(links)):
                all_points.extend(pts)
                while len(all_points) >= COLLECTION_BATCH_SIZE:
                    batch_to_insert = all_points[:COLLECTION_BATCH_SIZE]
                    client.upsert(collection_name=COLLECTION_NAME, points=batch_to_insert)
                    all_points = all_points[COLLECTION_BATCH_SIZE:]

        time.sleep(random.uniform(0.8, 1.5))

        if all_points:
            client.upsert(collection_name=COLLECTION_NAME, points=all_points)

    except Exception as e:
        print(e)
        time.sleep(10)

if __name__ == "__main__":
    main()
