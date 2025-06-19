from app.core.database import Base, engine
from app.models.user import User  # импортируем модель пользователя

def init_db():
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    print("База данных инициализирована.")

if __name__ == "__main__":
    init_db()
