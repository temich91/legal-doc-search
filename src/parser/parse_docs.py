from multiprocessing import Pool, cpu_count
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

SEARCH_PAGE_LINK = "https://sudrf.cntd.ru/search?type=777720157&startDate=2021-01-01&endDate=2025-12-01"
COLLECTION_NAME = "legal_fabulas"
EDGE_DRIVER_PATH = SRC_DIR / "parser" / "msedgedriver.exe"
MODEL_PATH = SRC_DIR / "model"
COLLECTION_BATCH_SIZE = 64
EMBEDDING_DIM = 768

model = None
chunker = None

def init_worker():
    global model, chunker
    model = RuLawEmbedder(MODEL_PATH)
    chunker = Chunker()
    print("worker init done")

def embed(link):
    global model, chunker
    paragraphs = chunker.get_paragraphs(link, without_title=True)  # 1 request
    chunks = chunker.chunk_paragraphs(paragraphs)
    if not chunks:
        return []
    time.sleep(random.uniform(1.0, 2.0))

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
        with Parser(EDGE_DRIVER_PATH) as parser:
            # Сбор ссылок со страницы поиска
            links_page = parser.get_links_list_page(SEARCH_PAGE_LINK, max_scroll=2)
            links = parser.get_docs_links(links_page) # заменить на parser.parse_all()
        print(f"Загружается {len(links)} ссылок")

        with Pool(processes=cpu_count() - 1, initializer=init_worker) as pool:
            for pts in tqdm(pool.imap_unordered(embed, links), total=len(links)):
                all_points.extend(pts)
                while len(all_points) >= COLLECTION_BATCH_SIZE:
                    batch_to_insert = all_points[:COLLECTION_BATCH_SIZE]
                    client.upsert(collection_name=COLLECTION_NAME, points=batch_to_insert)
                    all_points = all_points[COLLECTION_BATCH_SIZE:]

        if all_points:
            client.upsert(collection_name=COLLECTION_NAME, points=all_points)

    except Exception as e:
        print(e)
        time.sleep(10)

if __name__ == "__main__":
    main()
