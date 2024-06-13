"""
Асинхронный вариант сервиса
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.async_model import RecomModel

app = FastAPI()

# Инициализация модели рекомендаций
model = RecomModel()


class Resume(BaseModel):
    fio: str
    res_title: str
    City: str
    graph: str
    microcat_name: str
    res_des: str


@app.post("/recommend")
async def recommend(resume: Resume):
    try:
        recs_df = await model.recommend(resume.dict(), K=50)
        recommendations = recs_df[['vac_title', 'vac_des', 'Region', 'City',
                                   'microcat_name', 'graph', 'norm_score']].to_dict(orient='records')
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
