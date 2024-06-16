from fastapi import FastAPI, Depends, File, UploadFile, Response, HTTPException
import uvicorn
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from schemas import *
from database import get_db
from models import *
import csv
from algos import *
from to_bd import *
import io


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.delete("/init/")
async def root():
    #to_bd_graph()
    to_bd_shedule()
    return {"message": "success"}


@app.delete("/algos/")
async def root():
    algos()
    to_bd_algos_real()
    to_bd_algos_ideal()
    return {"message": "success"}


@app.get("/")
async def root():
    return {"message": "success"}


@app.post("/load_file/")
async def upload_excel(file: UploadFile = File(...)):

    try:
        if not file.filename.endswith((".xls", ".xlsx")):
            raise HTTPException(
                status_code=400, detail="Недопустимый формат файла. Пожалуйста, загрузите файл Excel (.xls, .xlsx)."
            )

        # df = pd.read_excel(file.file)
        # df.to_excel('load.xlsx')
        return {'m' : 'ok'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки файла: {str(e)}")


@app.get("/download_file_requests/")
async def root():
    filename = "shablon.xlsx"
    return FileResponse(filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        filename=filename)


@app.get("/map_info/")
async def root(ship_name : str, db: Session = Depends(get_db)):
    way = get_path_dots(ship_name)
    res = []
    for w in way:
        res.append(db.query(GraphData).filter(GraphData.point_name == w).first())
    return res


@app.get("/detailed_info/")
async def get_items(ship_name : str, db: Session = Depends(get_db)):
    way = get_path_dots(ship_name)
    res = []
    for w in way:
        res.append(db.query(GraphData).filter(GraphData.point_name == w).first())
    return {'ship' : db.query(Schedule).filter(Schedule.ship_name == ship_name).first(), 'points' : res}


@app.get("/list_ships/")
async def get_items(db: Session = Depends(get_db)):
    return db.query(Schedule).all()

@app.post("/new_request/")
async def create_emergency(sh: ScheduleItem, db: Session = Depends(get_db)):

    try:
        new_s = Schedule(**sh.dict())
        db.add(new_s)
        db.commit()
        return JSONResponse(
            status_code=201,
            content={"message": "Запись  успешно создана."}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при создании записи: {e}"
        )


@app.get("/list_ledokol/")
async def root():
    df = pd.read_csv('ledocol_anal.csv')
    return {
        '50 лет Победы' : f"{df.iloc[0]['50 лет Победы']}",
        'Ямал' :f"{df.iloc[0]['Ямал']}",
        'Таймыр' :f"{df.iloc[0]['Таймыр']}" ,
        'Вайгач' :f"{df.iloc[0]['Вайгач']}"
    }

@app.delete("/")
async def kill():
    os.kill(os.getpid(), 9)
    return {"message": "error"}

if __name__ == '__main__':
    uvicorn.run(app, port=8000)