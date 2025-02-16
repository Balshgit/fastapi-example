## Запуск интеграционных тестов

Поднять тестовую инфраструктуру для интеграционных тестов. Есть два возможных варианта запуска:

```bash
docker compose up -d
```

```bash
make up-dependencies
```


2. В файле `settings/envoronments/.env.local.runtests` определить название баз и порты:
```dotenv 
POSTGRES_DB_PORT="5433"
POSTGRES_DB="example_database_test"
POSTGRES_USER="user"
POSTGRES_PASSWORD="postgrespwd"
DB_HOST="localhost"

USER_KEY_HEADER="292ef340-608d-4c10-88fc-4537fa369560"

REDIS_USER="user"
REDIS_PASSWORD="redispwd"
REDIS_DATABASE="dragonfly_db.rdb"
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_BACKUP_DB: "*:*"
```

---

Запустить все тесты
```bash
LOCALTEST=1 pytest tests
```


Запустить только интеграционные тесты
```bash
LOCALTEST=1 pytest tests/integration
```

Запустить только unit тесты
```bash
LOCALTEST=1 pytest tests/unit
```

После прогона отключить все контейнеры, если они больше не нужны:

```bash
docker compose down -v
```

или же

```bash
make down-dependencies
```
