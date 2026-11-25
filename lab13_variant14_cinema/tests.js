// ЛР №13, вариант 14 — команды тестирования.
// Каждую группу выполняйте в ОТДЕЛЬНОМ окне mongosh.
// При подключении введите пароль интерактивно. Не вставляйте пароль в команду.

// Подключение viewer:
// mongosh --host 127.0.0.1 --port 27017 --authenticationDatabase cinema_lab13 -u viewer14 -p
use cinema_lab13
db.movies.findOne({ movieId: 1 })                 // РАЗРЕШЕНО
db.movies.insertOne({ movieId: 99, title: "Тест" }) // ЗАПРЕЩЕНО: ожидается Unauthorized
db.tickets.findOne({ ticketId: 1001 })            // ЗАПРЕЩЕНО: ожидается Unauthorized

// Подключение editor (новое окно):
// mongosh --host 127.0.0.1 --port 27017 --authenticationDatabase cinema_lab13 -u editor14 -p
use cinema_lab13
db.movies.findOne({ movieId: 1 })                 // РАЗРЕШЕНО
db.movies.insertOne({ movieId: 99, title: "Тест редактора", genre: "Тест", year: 2026, duration: 90 }) // РАЗРЕШЕНО
db.tickets.findOne({ ticketId: 1001 })            // ЗАПРЕЩЕНО: ожидается Unauthorized
db.audit_events.findOne({ eventId: 1 })           // ЗАПРЕЩЕНО: ожидается Unauthorized

// Подключение auditor (новое окно):
// mongosh --host 127.0.0.1 --port 27017 --authenticationDatabase cinema_lab13 -u auditor14 -p
use cinema_lab13
db.audit_events.findOne({ eventId: 1 })           // РАЗРЕШЕНО
db.audit_events.insertOne({ eventId: 99, event: "forbidden_test" }) // ЗАПРЕЩЕНО: ожидается Unauthorized
db.movies.findOne({ movieId: 1 })                 // ЗАПРЕЩЕНО: ожидается Unauthorized

// Проверка минимальных привилегий (выполнить под администратором):
// use cinema_lab13
// db.getRole("cinemaViewer", { showPrivileges: true })
// db.getRole("cinemaEditor", { showPrivileges: true })
// db.getRole("cinemaAuditor", { showPrivileges: true })
// Убедитесь, что каждый privilege.resource указывает ровно на одну коллекцию,
// а не на { db: "cinema_lab13", collection: "" } и не на { db: "cinema_lab13", collection: "*" }.
