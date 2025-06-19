from app.core.database import Base, engine
from app.models.user import User  # импортируем модель пользователя

# Вывод информации о метаданных
print('Таблицы в метаданных:')
for table in Base.metadata.tables.keys():
    print(f'- {table}')

# Создание таблиц
print('\nСоздание таблиц...')
Base.metadata.create_all(bind=engine)
print('Таблицы созданы.')
