# Telegram -> VK chats relay

Небольшой сервис на Python для отслеживания новых постов в Telegram-каналах через пользовательский аккаунт и отправки их в чаты ВКонтакте.

## Возможности

- подключение к Telegram через `Telethon`
- чтение настроек из `.env`
- чтение списка каналов из `config/channels.json`
- отправка текста в VK через `messages.send`
- попытка приложить фото к сообщению в VK
- понятное логирование запуска, публикаций и ошибок
- обработка ошибок без падения всего сервиса

## Структура проекта

```text
.
├── .env.example
├── README.md
├── config/
│   └── channels.json
├── main.py
├── requirements.txt
└── tg2vk/
    ├── __init__.py
    ├── app.py
    ├── config.py
    ├── logging_config.py
    ├── telegram_service.py
    └── vk_service.py
```

## Установка

1. Создайте и активируйте виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

## Настройка `.env`

1. Скопируйте пример:

```bash
cp .env.example .env
```

2. Заполните переменные:

- `TG_API_ID` - Telegram API ID
- `TG_API_HASH` - Telegram API HASH
- `TG_SESSION` - имя или путь к session-файлу Telethon
- `VK_ACCESS_TOKEN` - токен доступа VK с правами на отправку сообщений
- `VK_API_VERSION` - версия VK API, по умолчанию `5.199`
- `CHANNELS_CONFIG_PATH` - путь до JSON-файла с каналами, по умолчанию `config/channels.json`
- `LOG_LEVEL` - уровень логирования, по умолчанию `INFO`

## Настройка каналов

Отредактируйте файл `config/channels.json`:

```json
{
  "channels": [
    {
      "tg_channel": "@ZeRada1",
      "source_title": "ZeRada",
      "vk_peer_id": 2000000001
    },
    {
      "tg_channel": "@readovkanews",
      "source_title": "Readovka",
      "vk_peer_id": 2000000002
    }
  ]
}
```

- `tg_channel` - username канала с `@` или без него, либо числовой Telegram ID
- `source_title` - отображаемое имя источника в сообщении VK
- `vk_peer_id` - `peer_id` уже существующего чата или беседы VK, куда будет отправляться сообщение

Для беседы VK `peer_id` обычно равен `2000000000 + chat_id`.

## Запуск

```bash
python main.py
```

При первом запуске Telethon может запросить авторизацию пользовательского Telegram-аккаунта.

## Примечания

- сервис работает от имени пользовательского Telegram-аккаунта, не бота
- для отправки в VK используется `messages.send`
- маршрут Telegram канал -> VK чат полностью задается в `config/channels.json`
- если в сообщении есть фото, сервис пытается загрузить его и приложить к сообщению
- если загрузка фото не удалась, текст все равно будет отправлен
- если в Telegram пришло сообщение только с медиа без текста, сервис это залогирует и отправит сообщение с источником
