package kz.library;

import com.mongodb.client.*;
import com.mongodb.client.model.*;
import org.bson.Document;
import org.bson.types.ObjectId;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

import static com.mongodb.client.model.Filters.*;
import static com.mongodb.client.model.Sorts.*;

public class LibraryApp {
    private final MongoClient client;
    private final MongoDatabase db;
    private final MongoCollection<Document> books;
    private final MongoCollection<Document> readers;
    private final MongoCollection<Document> loans;

    public LibraryApp(String uri, String dbName) {
        client = MongoClients.create(uri);
        db = client.getDatabase(dbName);
        books = db.getCollection("books");
        readers = db.getCollection("readers");
        loans = db.getCollection("loans");
    }

    public void createIndexes() {
        books.createIndex(Indexes.ascending("title"));
        books.createIndex(Indexes.ascending("genre"));
        readers.createIndex(Indexes.ascending("readerId"), new IndexOptions().unique(true));
        loans.createIndex(Indexes.compoundIndex(Indexes.ascending("reader.readerId"), Indexes.descending("loanDate")));
        loans.createIndex(Indexes.compoundIndex(Indexes.ascending("status"), Indexes.ascending("dueDate")));
        loans.createIndex(Indexes.ascending("book.bookId"));
    }

    public void seedData() {
        books.deleteMany(new Document());
        readers.deleteMany(new Document());
        loans.deleteMany(new Document());

        String[] titles = {"Преступление и наказание","Евгений Онегин","Таинственный остров",
            "Убийство в Восточном экспрессе","Я, робот","Мастер и Маргарита","1984","Дюна",
            "Шерлок Холмс","Краткая история времени","Солярис","Фауст","Гарри Поттер",
            "О дивный новый мир","Три мушкетёра","Маленький принц","Одиссея","Алхимик",
            "Доктор Живаго","451 градус по Фаренгейту","Белый пароход","Айвенго","Моби Дик",
            "Граф Монте-Кристо","Пикник на обочине","Анна Каренина","Марсианин",
            "Война и мир","Робинзон Крузо","Цветы для Элджернона"};
        String[] genres = {"Роман","Фантастика","История","Детектив","Наука"};
        String[] authors = {"Ф. Достоевский","А. Пушкин","Ж. Верн","А. Кристи","А. Азимов",
            "М. Булгаков","Ч. Айтматов","Дж. Оруэлл"};
        List<Document> bookDocs = new ArrayList<>();
        for (int i=0; i<titles.length; i++) {
            bookDocs.add(new Document("bookId", String.format("B%03d", i+1))
                .append("title", titles[i]).append("author", authors[i % authors.length])
                .append("genre", genres[i % genres.length]).append("year", 1950 + (i*3)%74)
                .append("copies", 1 + i%4));
        }
        books.insertMany(bookDocs);

        List<Document> readerDocs = new ArrayList<>();
        for (int i=1; i<=15; i++) readerDocs.add(new Document("readerId", String.format("R%03d", i))
            .append("name", String.format("Читатель %02d", i)).append("email", "reader"+i+"@example.test"));
        readers.insertMany(readerDocs);

        List<Document> loanDocs = new ArrayList<>();
        Instant now = Instant.now();
        for (int i=1; i<=45; i++) {
            Document b = bookDocs.get((i*7)%bookDocs.size());
            Document r = readerDocs.get((i*3)%readerDocs.size());
            Instant loanDate = now.minus((i*5L)%55, ChronoUnit.DAYS);
            boolean overdue = i%5==0;
            boolean returned = i%3==0;
            Instant dueDate = loanDate.plus(overdue ? 7 : 14, ChronoUnit.DAYS);
            Document bookSnap = new Document("bookId", b.getString("bookId"))
                .append("title", b.getString("title")).append("author", b.getString("author"))
                .append("genre", b.getString("genre"));
            Document readerSnap = new Document("readerId", r.getString("readerId")).append("name", r.getString("name"));
            loanDocs.add(new Document("book", bookSnap).append("reader", readerSnap)
                .append("loanDate", Date.from(loanDate)).append("dueDate", Date.from(dueDate))
                .append("returnDate", returned ? Date.from(loanDate.plus(10, ChronoUnit.DAYS)) : null)
                .append("status", returned ? "returned" : "issued"));
        }
        loans.insertMany(loanDocs);
        System.out.println("Добавлены 30 книг, 15 читателей и 45 выдач.");
    }

    public void addBook(String id, String title, String author, String genre) {
        books.insertOne(new Document("bookId", id).append("title", title).append("author", author)
            .append("genre", genre).append("year", Calendar.getInstance().get(Calendar.YEAR)).append("copies", 1));
    }

    public void issueBook(String bookId, String readerId) {
        Document b = books.find(eq("bookId", bookId)).first();
        Document r = readers.find(eq("readerId", readerId)).first();
        if (b == null || r == null) throw new IllegalArgumentException("Книга или читатель не найдены.");
        Date now = new Date();
        Document bookSnap = new Document("bookId", b.getString("bookId")).append("title", b.getString("title"))
            .append("author", b.getString("author")).append("genre", b.getString("genre"));
        Document readerSnap = new Document("readerId", r.getString("readerId")).append("name", r.getString("name"));
        loans.insertOne(new Document("book", bookSnap).append("reader", readerSnap).append("loanDate", now)
            .append("dueDate", Date.from(now.toInstant().plus(14, ChronoUnit.DAYS)))
            .append("returnDate", null).append("status", "issued"));
    }

    public boolean returnLoan(String objectId) {
        return loans.updateOne(and(eq("_id", new ObjectId(objectId)), eq("status", "issued")),
            Updates.combine(Updates.set("status", "returned"), Updates.set("returnDate", new Date()))).getModifiedCount() == 1;
    }

    public boolean deleteLoan(String objectId) {
        return loans.deleteOne(eq("_id", new ObjectId(objectId))).getDeletedCount() == 1;
    }

    public List<Document> allBooks() { return books.find().sort(ascending("title")).into(new ArrayList<>()); }
    public List<Document> findBooks(String text) { return books.find(regex("title", text, "i")).into(new ArrayList<>()); }
    public List<Document> readerHistory(String readerId) { return loans.find(eq("reader.readerId", readerId)).sort(descending("loanDate")).into(new ArrayList<>()); }
    public List<Document> overdueLoans() { return loans.find(and(eq("status","issued"), lt("dueDate", new Date()))).into(new ArrayList<>()); }
    public List<Document> availableBooks() {
        Set<String> issued = new HashSet<>();
        for (Document d : loans.find(eq("status","issued"))) issued.add(d.get("book", Document.class).getString("bookId"));
        return books.find(nin("bookId", issued)).sort(ascending("title")).into(new ArrayList<>());
    }
    public List<Document> popularBooks() {
        List<Document> pipeline = Arrays.asList(
            new Document("$group", new Document("_id", "$book.bookId")
                .append("title", new Document("$first", "$book.title")).append("count", new Document("$sum", 1))),
            new Document("$sort", new Document("count", -1).append("title", 1)),
            new Document("$limit", 10));
        return loans.aggregate(pipeline).into(new ArrayList<>());
    }
    public List<Document> loansByGenre() {
        List<Document> pipeline = Arrays.asList(
            new Document("$group", new Document("_id", "$book.genre").append("count", new Document("$sum", 1))),
            new Document("$sort", new Document("count", -1)));
        return loans.aggregate(pipeline).into(new ArrayList<>());
    }
    public long countBooks() { return books.countDocuments(); }
    public long countReaders() { return readers.countDocuments(); }
    public long countLoans() { return loans.countDocuments(); }
    public void close() { client.close(); }

    public static void main(String[] args) {
        String uri = System.getenv().getOrDefault("MONGODB_URI", "mongodb://localhost:27017");
        try (Scanner scanner = new Scanner(System.in)) {
            LibraryApp app = new LibraryApp(uri, "library_nosql");
            try {
                app.createIndexes();
                System.out.println("Библиотека — вариант 3 (Java + MongoDB)");
                System.out.println("1 Заполнить тестовыми данными  2 Все книги  3 Поиск по названию");
                System.out.println("4 История читателя  5 Просрочки  6 Популярные книги");
                System.out.println("7 Статистика жанров  8 Добавить книгу  9 Выдать книгу  10 Возврат  11 Удалить выдачу");
                System.out.print("Выбор: ");
                String choice = scanner.nextLine().trim();
                switch (choice) {
                    case "1" -> app.seedData();
                    case "2" -> app.allBooks().forEach(System.out::println);
                    case "3" -> { System.out.print("Фрагмент названия: "); app.findBooks(scanner.nextLine()).forEach(System.out::println); }
                    case "4" -> { System.out.print("ID читателя (R001): "); app.readerHistory(scanner.nextLine()).forEach(System.out::println); }
                    case "5" -> app.overdueLoans().forEach(System.out::println);
                    case "6" -> app.popularBooks().forEach(System.out::println);
                    case "7" -> app.loansByGenre().forEach(System.out::println);
                    case "8" -> {
                        System.out.print("ID книги: "); String id=scanner.nextLine();
                        System.out.print("Название: "); String title=scanner.nextLine();
                        System.out.print("Автор: "); String author=scanner.nextLine();
                        System.out.print("Жанр: "); String genre=scanner.nextLine();
                        app.addBook(id,title,author,genre); System.out.println("Книга добавлена.");
                    }
                    case "9" -> {
                        System.out.print("ID книги: "); String b=scanner.nextLine();
                        System.out.print("ID читателя: "); String r=scanner.nextLine();
                        app.issueBook(b,r); System.out.println("Выдача оформлена.");
                    }
                    case "10" -> { System.out.print("ObjectId выдачи: "); System.out.println(app.returnLoan(scanner.nextLine()) ? "Возврат выполнен." : "Выдача не найдена/закрыта."); }
                    case "11" -> { System.out.print("ObjectId выдачи: "); System.out.println(app.deleteLoan(scanner.nextLine()) ? "Выдача удалена." : "Выдача не найдена."); }
                    default -> System.out.println("Неизвестный пункт.");
                }
            } finally { app.close(); }
        }
    }
}
