# School Auth System

Система аутентификации и авторизации для школы с разграничением доступа.

## Схема БД
```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    СХЕМА БД "ШКОЛА"                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│      users       │     │    user_roles    │     │      roles       │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ id (PK)          │────<│ user_id (FK)     │ ┌───│ id (PK)          │
│ email (unique)   │     │ role_id (FK)     │>┘   │ name             │
│ password_hash    │     └──────────────────┘     │ description      │
│ full_name        │                              └──────────────────┘
│ is_active        │
│ created_at       │     ┌──────────────────┐     ┌──────────────────┐
│ updated_at       │     │ parent_student   │     │    classes       │
│ class_id (FK)    │──┐  ├──────────────────┤     ├──────────────────┤
└──────────────────┘  │  │ id (PK)          │     │ id (PK)          │
         │            │  │ parent_id (FK)   │>──┐ │ name (5А, 9Б)    │
         │            │  │ student_id (FK)  │───┼>│ year (2025)      │
         │            │  └──────────────────┘   │ └──────────────────┘
         │            │                         │          │
         │            │                         │          │
         │            │                         │          │
         │            │                         │          │
         │            │                         │          │
         │            │                         │          ▼
         │            │                         │   ┌──────────────────┐
         │            │                         │   │  class_subjects  │
         │            │                         │   ├──────────────────┤
         │            │                         │   │ id (PK)          │
         │            │                         │   │ class_id (FK)    │>──┐
         │            │                         │   │ subject_id (FK)  │   │
         │            │                         │   │ is_optional      │   │
         │            │                         │   └──────────────────┘   │
         │            │                         │                          │
         │            │                         │   ┌──────────────────┐   │
         │            │                         │   │    subjects      │   │
         │            │                         │   ├──────────────────┤   │
         │            │                         │   │ id (PK)          │<──┘
         │            │                         │   │ name (Химия)     │
         │            │                         │   │ description      │
         │            │                         │   └──────────────────┘
         │            │                         │
         │            │                         │   ┌──────────────────────────┐
         │            │                         │   │ teacher_class_subject    │
         │            │                         │   ├──────────────────────────┤
         │            │                         │   │ id (PK)                  │
         │            │                         └──>│ class_subject_id (FK)    │
         │            │                             │ teacher_id (FK)          │>──┐
         │            │                             │ (ссылка на users.id)     │   │
         │            │                             └──────────────────────────┘   │
         │            │                                                            │
         │            │   ┌──────────────────┐                                     │
         │            │   │      grades      │                                     │
         │            │   │   (журнал)       │                                     │
         │            │   ├──────────────────┤                                     │
         │            │   │ id (PK)          │                                     │
         │            └──>│ student_id (FK)  │                                     │
         │                │ class_subject_id │>────────────────────────────────────┘
         │                │   (FK)           │
         │                │ grade (2-5)      │
         ├───────────────<│ teacher_id (FK)  │
         │                │ deleted_at       │                                       
         └───────────────<│ deleted_by (FK)  │
                          │ comment          │                                  
                          └──────────────────┘                                  
                                                                                  
            ┌──────────────────┐     ┌──────────────────┐                         
            │  permissions     │     │role_permissions  │                         
            ├──────────────────┤     ├──────────────────┤                         
            │ id (PK)          │<────│ id (PK)          │                         
            │ resource_type    │     │ role_id (FK)     │                         
            │ action (CRUD)    │     │ permission_id(FK)│                         
            └──────────────────┘     └──────────────────┘                         
                                                                                  
            ┌──────────────────┐     ┌──────────────────┐                         
            │  schedule        │     │  inventory       │     ┌──────────────────┐
            │  (расписание)    │     │  (инвентарь)     │     │      menu        │
            ├──────────────────┤     ├──────────────────┤     ├──────────────────┤
            │ id (PK)          │     │ id (PK)          │     │ id (PK)          │
            │ class_id (FK)    │     │ name             │     │ date             │
            │ subject_id (FK)  │     │ quantity         │     │ dish_name        │
            │ teacher_id (FK)  │     │ status (new/bad) │     │ description      │
            │ day_of_week      │     │ updated_by (FK)  │     │ updated_by (FK)  │
            │ lesson_number    │     └──────────────────┘     └──────────────────┘
            └──────────────────┘                                                  
                                                                                  
            ┌──────────────────┐                                                  
            │ token_blacklist  │                                                  
            ├──────────────────┤                                                  
            │ id (PK)          │                                                  
            │ token_fingerprint│                                                  
            │ expires_at       │                                                  
            │ revoked_at       │                                                  
            └──────────────────┘                                                  

```


## Основные таблицы:
- `users` — пользователи (ученики, учителя, родители, директор, завхоз, повар)
- `roles` — роли (admin, director, teacher, parent, student, caretaker, cook)
- `permissions` — разрешения (resource_type + action)
- `user_roles`, `role_permissions` — связующие таблицы
- `classes`, `subjects`, `class_subjects`, `teacher_class_subject` — школьная структура
- `grades` — журнал оценок с мягким удалением
- `parent_student` — связь родитель-ученик
- `token_blacklist` — отозванные токены

## Правила доступа

| Роль | Что может |
|------|-----------|
| admin | Всё |
| director | Чтение всего, составление расписания |
| teacher | Чтение всех оценок, запись/удаление только по своему предмету |
| parent | Чтение оценок и расписания только своего ребёнка |
| student | Чтение своих оценок и расписания |
| caretaker | Управление инвентарём |
| cook | Управление меню |

## Технологии

- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Bearer-токены

## Подготовка базы данных
Перед первым запуском создайте базу данных PostgreSQL:

```bash
sudo -u postgres psql
CREATE DATABASE school_auth;
CREATE USER school_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE school_auth TO school_user;
\q
```


## Настройка .env

Создайте файл `.env` в корне проекта:  

```bash
DATABASE_URL=postgresql+asyncpg://school_user:your_password@localhost/school_auth
```

# Установка зависимостей

```bash
pip install -r requirements.txt
```

# Запуск и тестирование

1.  Запустите сервер:
    ```bash
    uvicorn app.main:app
    ```
2. После запуска, интерактивная документация API (с возможностью тестирования) доступна по адресам:

    Swagger UI: http://localhost:8000/docs

    ReDoc: http://localhost:8000/redoc



## Тестовые пользователи
Все с паролем `pass`:

Роль |	Email
-----|--------
Учитель математики |	t_math@sch.com
Ученик (5А)	 |s1@sch.com
Ученик (6А)	 |s2@sch.com
Родитель	 |p@sch.com
Директор |	d@sch.com
Завхоз |	care@sch.com
Повар |	cook@sch.com


## API Endpoints
### Аутентификация
`POST /auth/register` — регистрация  
`POST /auth/login` — вход  
`POST /auth/logout` — выход  
`GET /auth/me` — профиль  

### Пользователи
`GET /users` — список (админ → все, иначе → только себя)

### Журнал оценок
`GET /grades` — получить оценки (с разной фильтрацией по роли)  
`POST /grades` — поставить оценку (учитель)  
`DELETE /grades/{id}` — мягкое удаление с комментарием (учитель)  

### Администрирование (только admin)

#### Управление ролями
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/admin/roles` | Создать роль |
| GET | `/admin/roles` | Список всех ролей |
| DELETE | `/admin/roles/{role_id}` | Удалить роль |

#### Управление ролями пользователей
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/admin/users/{user_id}/roles/{role_id}` | Назначить роль пользователю |
| DELETE | `/admin/users/{user_id}/roles/{role_id}` | Снять роль с пользователя |
| GET | `/admin/users/{user_id}/roles` | Получить роли пользователя |

#### Управление разрешениями
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/admin/permissions` | Создать разрешение |
| POST | `/admin/roles/{role_id}/permissions/{permission_id}` | Назначить разрешение роли |
| DELETE | `/admin/roles/{role_id}/permissions/{permission_id}` | Снять разрешение с роли |

## Коды ответов

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 401 | Не авторизован (нет токена или токен невалиден) |
| 403 | Доступ запрещён (нет прав на ресурс) |
| 404 | Ресурс не найден |
| 422 | Ошибка валидации данных |

## Логика проверки прав

### Журнал оценок (`GET /grades`)
| Роль | Что видит |
|------|-----------|
| director / admin | Все оценки |
| teacher | Только оценки по предметам, которые ведёт |
| parent | Только оценки своих детей |
| student | Только свои оценки |

### Постановка оценки (`POST /grades`)
- Только пользователь с ролью `teacher`
- Учитель должен быть привязан к предмету через `teacher_class_subject`
- Ученик должен учиться в классе, где этот предмет изучается

### Удаление оценки (`DELETE /grades/{id}`)
- Только учитель, который ведёт этот предмет
- Мягкое удаление: заполняются `deleted_at`, `deleted_by`, `comment`
- Оценка не удаляется физически из БД


### Особенности
Мягкое удаление аккаунта (is_active=False)  
Мягкое удаление оценок с комментарием причины    

## Технологии
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Bearer-токены (UUID, хранятся в памяти сервера)

## Структура проекта
```text
.
├── app
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── lifespan.py
│   └── schemas.py
├── main.py
├── models
│   ├── base.py
│   ...
│   └── user_role.py
├── README.md
├── requirements.txt
└── routers
    ├── admin_router.py
    ├── auth_router.py
    ├── grades_router.py
    └── user_router.py
```