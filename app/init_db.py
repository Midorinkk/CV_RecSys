import pyarrow.parquet as pq
import compress_fasttext

from qdrant_client import QdrantClient
from qdrant_client import models

from tqdm import tqdm

dataset = pq.ParquetDataset('./app/data/all_embs.parquet')
df_with_embeddings = dataset.read(use_threads=True).to_pandas()

model_path = './app/geowac_tokens_sg_300_5_2020-400K-100K-300.bin' 
FT_MODEL = compress_fasttext.models.CompressedFastTextKeyedVectors.load(model_path)

# создаем клиент бд
QDRANT_CLIENT = QdrantClient(host='qdrant', port=6333)

COLLECTION_NAME = "vacancies"
VECTOR_SIZE = 300
DISTANCE_METRIC = models.Distance.COSINE

# Проверяем существование коллекции
if not QDRANT_CLIENT.collection_exists(collection_name=COLLECTION_NAME):
    # Если коллекции не существует, создаем её
    QDRANT_CLIENT.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=DISTANCE_METRIC)
    )
    print(f"Коллекция '{COLLECTION_NAME}' успешно создана.")

    vectors = df_with_embeddings['embedding'].tolist()
    payload = df_with_embeddings.drop(columns=['embedding']).to_dict(orient='records')

    # Функция для загрузки данных по батчам
    def upload_in_batches(client, collection_name, vectors, payload, batch_size=256):
        for i in tqdm(range(0, len(vectors), batch_size)):
            batch_vectors = vectors[i:i+batch_size]
            batch_payload = payload[i:i+batch_size]
            client.upload_collection(
                collection_name=collection_name,
                vectors=batch_vectors,
                payload=batch_payload,
                batch_size=batch_size
            )

    # Загрузите данные в Qdrant по батчам
    upload_in_batches(QDRANT_CLIENT, 'vacancies', vectors, payload)