"""
Модель рекомендаций
"""
import compress_fasttext

from qdrant_client import QdrantClient
from qdrant_client import models

import pandas as pd
import numpy as np

from collections import defaultdict
import json
import re

# from app.init_db import FT_MODEL, QDRANT_CLIENT


# словарь {город: регион} для городов с <100 вакансий в базе
# нужно для формирования жесткого фильтра
with open('./app/data/small_mappings.json', 'r') as f:
    SMALL_MAPPINGS = json.load(f)

# создаем модель
model_path = './app/geowac_tokens_sg_300_5_2020-400K-100K-300.bin' 
FT_MODEL = compress_fasttext.models.CompressedFastTextKeyedVectors.load(model_path)

# создаем клиент бд
QDRANT_CLIENT = QdrantClient(host='qdrant', port=6333)


class RecomModel:
    def __init__(self,
                 small_mappings: dict=SMALL_MAPPINGS):
        self.model = FT_MODEL
        self.qdrant_client = QDRANT_CLIENT

        self.small_mappings = small_mappings
        self.soft_filters = {'City': 2,
                             'graph': 1,
                             'microcat_name': 1}
        
    def clean_text(self, text: str) -> str:
        """
        удаляет нежелательные символы, приводит к нижнему регистру

        text: str - исходный текст
        ---
        output: str - обработанный текст
        """
        # Удаление нежелательных символов и чисел
        text = re.sub(r'[^а-яА-ЯёЁ\s]', '', text)

        # Приведение текста к нижнему регистру
        text = text.lower()

        # Токенизация текста
        words = text.split()

        # Объединение слов обратно в строку
        preprocessed_text = ' '.join(words)

        return preprocessed_text

    async def get_embedding(self, text: str) -> np.array:
        """
        получение эмбеддинга текста

        text: str
        ---
        output: np.array - эмбеддинг
        """
        return self.model.get_sentence_vector(self.clean_text(text)).astype(np.float16)
    
    async def get_combined_embedding(self,
                                     title: str,
                                     text: str,
                                     title_weight:float=0.4) -> np.array:
        """
        получение эмбеддинга из заголовка и основного текста

        title: str - заголовок
        text: str - основной текст
        title_weight: float=0.6 - вес заголовка в эмбеддинге
        ---
        output: np.array - финальный эмбеддинг
        """
        title_embedding = await self.get_embedding(title)
        text_embedding = await self.get_embedding(text)
        
        combined_embedding = title_weight * title_embedding + (1 - title_weight) * text_embedding
        return combined_embedding
    
    
    async def hard_filters(self,
                           res_city: str,
                           res_graph: str):
        """
        формирует жесткие фильтры

        res_city: str - город из резюме
        res_graph: str - график работы из резюме
        ---
        output: models.Filter - жесткие фильтры
        """
        qfilter = None
        if res_graph not in ['Удаленная работа', 'Вахтовый']:
            if res_city in SMALL_MAPPINGS:
                qfilter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="Region",
                            match=models.MatchValue(
                                value=SMALL_MAPPINGS[res_city],
                            ),
                        )
                    ]
                )
            else:
                qfilter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="City",
                            match=models.MatchValue(
                                value=res_city,
                            ),
                        )
                    ]
                )
        return qfilter
    
    async def recommend(self,
                        res: dict,
                        K:int=50) -> pd.DataFrame:
        """
        рекомендует top-K вакансий к резюме
        
        res: dict - словарь с характеристиками резюме 
        K: int=50 - кол-во рекомендаций в выдаче
        ---
        output: pd.DataFrame - датафрейм с предсказаниями
        """
        # получаем эмбеддинг резюме
        res_emb = await self.get_combined_embedding(res['res_title'], res['res_des'])

        # получаем жесткие фильтры
        qfilter = await self.hard_filters(res['City'], res['graph'])

        # получаем К * 5 кандидатов
        relevant_vacancies = self.qdrant_client.search(
                                collection_name='vacancies',
                                query_vector=res_emb,
                                limit=K * 10,
                                query_filter=qfilter
                            )

        # накладываем мягкие фильтры: увеличиваем схожесть по городу, графику и сфере
        vac_data = defaultdict(list)
        for vac in relevant_vacancies:
            score = vac.score
            city = vac.payload['City']
            graph = vac.payload['graph']
            microcat = vac.payload['microcat_name']

            vac_data['Item_id'].append(vac.payload['Item_id'])
            vac_data['City'].append(city)
            vac_data['Region'].append(vac.payload['Region'])
            vac_data['graph'].append(graph)
            vac_data['microcat_name'].append(microcat)
            vac_data['vac_title'].append(vac.payload['vac_title'])
            vac_data['vac_des'].append(vac.payload['vac_des'])

            if city == res['City']:
                score += self.soft_filters['City']
            if graph == res['graph']:
                score += self.soft_filters['graph']
            if microcat == res['microcat_name']:
                score += self.soft_filters['microcat_name']

            vac_data['score'].append(score)

        candidates_df = pd.DataFrame(vac_data)

        # нормируем скор
        candidates_df['norm_score'] = ((candidates_df['score'] - candidates_df['score'].min())
                                    /(candidates_df['score'].max() - candidates_df['score'].min()))

        # формируем финальные предсказания
        recs_df = candidates_df.sort_values(by='norm_score', ascending=False).head(K)
        return recs_df
