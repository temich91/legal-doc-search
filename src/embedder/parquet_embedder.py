import pyarrow as pa
import pyarrow.parquet as pq
from rulaw_embedder import RuLawEmbedder
from tqdm import tqdm

class ParquetEmbedder:
    def __init__(self, embedder, text_col_name="textIPS", batch_size=8, max_length=512):
        self.embedder = embedder
        self.text_col_name = text_col_name
        self.batch_size = batch_size
        self.max_length = max_length

    def encode_parquet(self, input_path="text0.parquet", output_path="text0_proc.parquet"):
        parquet = pq.ParquetFile(input_path)

        for i in tqdm(range(parquet.num_row_groups), desc="Row groups processed:", position=0, leave=True):
            group = parquet.read_row_group(i, columns=[self.text_col_name])
            text_chunk_array = group.column(self.text_col_name)
            texts = []
            for chunk in text_chunk_array.chunks:
                texts.extend(chunk.to_pylist())

            texts = ["" if t is None else str(t) for t in texts]
            embeddings = self.embedder.get_embedding(texts, self.max_length)
            embedding_array = pa.array(embeddings.tolist(), type=pa.list_(pa.float32()))

            out_table = pa.Table.from_arrays([embedding_array], names=["embedding"])

            pq_writer = pq.ParquetWriter(output_path, out_table.schema, compression="SNAPPY")
            pq_writer.write_table(out_table)
            pq_writer.close()

pe = ParquetEmbedder(RuLawEmbedder())
pe.encode_parquet()
