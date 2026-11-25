// ЛР №13, вариант 14 — Кинотеатр
// Запускать ОДИН РАЗ из mongosh под администратором.
// Пароли вводятся интерактивно и в файл не записываются.

const lab = db.getSiblingDB("cinema_lab13");

// Коллекции варианта:
// movies       — рабочая коллекция
// tickets      — защищённая коллекция
// audit_events — отдельный журнал для аудитора

lab.createCollection("movies");
lab.createCollection("tickets");
lab.createCollection("audit_events");

// 10 синтетических фильмов
lab.movies.insertMany([
  { movieId: 1, title: "Звёздный маршрут", genre: "Фантастика", year: 2022, duration: 118 },
  { movieId: 2, title: "Тихий город", genre: "Драма", year: 2021, duration: 104 },
  { movieId: 3, title: "Последний рубеж", genre: "Боевик", year: 2023, duration: 126 },
  { movieId: 4, title: "Лесные истории", genre: "Приключения", year: 2020, duration: 97 },
  { movieId: 5, title: "Код времени", genre: "Фантастика", year: 2024, duration: 112 },
  { movieId: 6, title: "Смешной случай", genre: "Комедия", year: 2019, duration: 91 },
  { movieId: 7, title: "За горизонтом", genre: "Приключения", year: 2022, duration: 109 },
  { movieId: 8, title: "Старая площадь", genre: "Драма", year: 2018, duration: 121 },
  { movieId: 9, title: "Ночной сигнал", genre: "Триллер", year: 2023, duration: 101 },
  { movieId: 10, title: "Маленькая планета", genre: "Мультфильм", year: 2024, duration: 88 }
]);

// 10 синтетических билетов. Роли viewer/editor/auditor не должны иметь к ним доступа.
lab.tickets.insertMany([
  { ticketId: 1001, movieId: 1, seat: "A1", price: 2500, status: "sold" },
  { ticketId: 1002, movieId: 1, seat: "A2", price: 2500, status: "sold" },
  { ticketId: 1003, movieId: 2, seat: "B1", price: 2200, status: "reserved" },
  { ticketId: 1004, movieId: 3, seat: "C4", price: 2800, status: "sold" },
  { ticketId: 1005, movieId: 4, seat: "D2", price: 2000, status: "available" },
  { ticketId: 1006, movieId: 5, seat: "A5", price: 2700, status: "sold" },
  { ticketId: 1007, movieId: 6, seat: "E3", price: 1800, status: "available" },
  { ticketId: 1008, movieId: 7, seat: "F1", price: 2300, status: "reserved" },
  { ticketId: 1009, movieId: 8, seat: "B5", price: 2100, status: "sold" },
  { ticketId: 1010, movieId: 9, seat: "C2", price: 2600, status: "available" }
]);

// Журнал аудита: синтетические записи
lab.audit_events.insertMany([
  { eventId: 1, event: "database_created", source: "lab_setup", level: "info" },
  { eventId: 2, event: "movies_seeded", source: "lab_setup", level: "info" },
  { eventId: 3, event: "tickets_seeded", source: "lab_setup", level: "info" }
]);

// Пользовательские роли: права выданы только на конкретные коллекции.
lab.createRole({
  role: "cinemaViewer",
  privileges: [
    { resource: { db: "cinema_lab13", collection: "movies" }, actions: ["find"] }
  ],
  roles: []
});

lab.createRole({
  role: "cinemaEditor",
  privileges: [
    { resource: { db: "cinema_lab13", collection: "movies" },
      actions: ["find", "insert", "update", "remove"] }
  ],
  roles: []
});

lab.createRole({
  role: "cinemaAuditor",
  privileges: [
    { resource: { db: "cinema_lab13", collection: "audit_events" }, actions: ["find"] }
  ],
  roles: []
});

// Создание пользователей. Введите три разных учебных пароля при запросе.
lab.createUser({
  user: "viewer14",
  pwd: passwordPrompt(),
  roles: [{ role: "cinemaViewer", db: "cinema_lab13" }]
});

lab.createUser({
  user: "editor14",
  pwd: passwordPrompt(),
  roles: [{ role: "cinemaEditor", db: "cinema_lab13" }]
});

lab.createUser({
  user: "auditor14",
  pwd: passwordPrompt(),
  roles: [{ role: "cinemaAuditor", db: "cinema_lab13" }]
});

print("Готово: база cinema_lab13, коллекции, данные, роли и пользователи созданы.");
print("Проверьте количество документов:");
print("movies = " + lab.movies.countDocuments());
print("tickets = " + lab.tickets.countDocuments());
print("audit_events = " + lab.audit_events.countDocuments());
