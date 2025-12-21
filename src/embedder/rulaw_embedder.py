import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
from sentence_transformers.models import Pooling

class RuLawEmbedder:
    """
    Преобразование текстов в эмбеддинги с помощью модели ruBERT-ruLaw.
    """

    def __init__(self, model_path="model/",
                 cache_dir=None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Среда выполнения: {self.device}")
        self.cache_dir = cache_dir

        print("Инициализация модели")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, cache_dir=cache_dir)
        self.model = AutoModel.from_pretrained(model_path, cache_dir=cache_dir).to(self.device)

        self.model.eval()
        self.pooling = Pooling(768, pooling_mode="mean")
        self.embeddings = None

    def get_embedding(self, texts, max_length=512, batch_size=8):
        if isinstance(texts, str):
            texts = [texts]

        all_embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Text batches processed", position=0, leave=True):
            text_batch = texts[i:i + batch_size]

            inputs = self.tokenizer(
                text_batch,
                return_tensors="pt",
                truncation=True,
                padding="max_length",
                max_length=max_length
            )

            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)

            attention_mask = inputs["attention_mask"]

            embedding = self.pooling({"token_embeddings": outputs.last_hidden_state, "attention_mask": attention_mask})["sentence_embedding"].to(torch.float32)
            all_embeddings.append(embedding.detach())

            del inputs, outputs
            torch.cuda.empty_cache()

        self.embeddings = torch.cat(all_embeddings, dim=0).cpu().numpy()
        return self.embeddings
