FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
RUN apt-get install -y git-lfs
RUN git lfs install
RUN git lfs pull

RUN mkdir /app

COPY ./requirements.txt /app

WORKDIR /app

RUN python -m pip install -r requirements.txt
    
COPY . /app

# Загрузка и установка модели fasttext
RUN curl -LO https://github.com/avidale/compress-fasttext/releases/download/gensim-4-draft/geowac_tokens_sg_300_5_2020-400K-100K-300.bin && \
        mv geowac_tokens_sg_300_5_2020-400K-100K-300.bin ./app/geowac_tokens_sg_300_5_2020-400K-100K-300.bin

EXPOSE 8000 8501

CMD ["sh", "-c", "uvicorn app.async_back:app --host 0.0.0.0 --port 8000 & streamlit run app/async_front.py --server.port 8501 --server.address 0.0.0.0"]
