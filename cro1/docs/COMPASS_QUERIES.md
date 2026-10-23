# Запросы для проверки в MongoDB Compass

Выберите базу `library_nosql` и коллекцию `books`, `readers` или `loans`.

1. Все активные выдачи: Filter
```json
{"status":"issued"}
```
2. Просроченные выдачи: Filter (дату замените актуальной ISODate в Compass)
```json
{"status":"issued","dueDate":{"$lt":{"$date":"2026-10-23T00:00:00.000Z"}}}
```
3. История читателя:
```json
{"reader.readerId":"R001"}
```
4. Поиск книги по названию:
```json
{"title":{"$regex":"робот","$options":"i"}}
```
5. Популярность книг — вкладка Aggregations:
```json
[
 {"$group":{"_id":"$book.bookId","title":{"$first":"$book.title"},"count":{"$sum":1}}},
 {"$sort":{"count":-1}},
 {"$limit":10}
]
```
6. Статистика по жанрам — вкладка Aggregations:
```json
[
 {"$group":{"_id":"$book.genre","count":{"$sum":1}}},
 {"$sort":{"count":-1}}
]
```
