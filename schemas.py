from pydantic import BaseModel

# Модель Pydantic для валидации данных
class ScheduleItem(BaseModel):
    ship_name: str
    id_karavan: int
    id_provodki: int
    ice_class: int
    speed: int
    start_point: str
    end_point: str
    start_date: str
    karavan_point: str
    ledokol: str
    finish_time_plan: str
    finish_time_actual: str

