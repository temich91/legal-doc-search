from src.embedder.rulaw_embedder import RuLawEmbedder
from qdrant_client import QdrantClient
from paths import SRC_DIR

class RAGSearchClient:
    def __init__(self, qdrant_host: str, qdrant_port: int, collection_name, embedding_model):
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        self.model = embedding_model

    def search(self, query, limit= 10, score_threshold = None, unique_by_link= True):
        """
        Выполняет semantic search по чанкам

        :param query: текст запроса
        :param limit: сколько чанков вернуть
        :param score_threshold: минимальная похожесть (опционально)
        :param unique_by_link: возвращать только 1 чанк на документ
        """
        query_vector = self.model.get_embedding([query])[0]

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist(),
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        ).points

        output = []
        seen_links = set()

        for point in results:
            payload = point.payload
            link = payload["link"]

            if unique_by_link and link in seen_links:
                continue

            output.append({
                "score": round(point.score, 4),
                "text": payload["text"],
                "link": link,
            })

            seen_links.add(link)

        return output

if __name__ == "__main__":
    model_dir = SRC_DIR / "model"
    model = RuLawEmbedder(model_dir)

    client = RAGSearchClient(qdrant_host="localhost",
                             qdrant_port=6333,
                             collection_name="legal_fabulas",
                             embedding_model=model)
    query = input("Введите запрос:")
    n = 5
    outputs = client.search(query=query,
                  limit=n)
    print(outputs)
    for i in range(len(outputs)):
        print(f"{i + 1}) score={outputs[i]['score']} ссылка={outputs[i]['link']}")
