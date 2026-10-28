

CREATE CONSTRAINT reader_id_unique IF NOT EXISTS
FOR (r:Reader) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT book_id_unique IF NOT EXISTS
FOR (b:Book) REQUIRE b.id IS UNIQUE;

CREATE CONSTRAINT author_id_unique IF NOT EXISTS
FOR (a:Author) REQUIRE a.id IS UNIQUE;

MERGE (r1:Reader {id: 1}) SET r1.name = "Али", r1.age = 19, r1.group = "ИС-24-1";
MERGE (r2:Reader {id: 2}) SET r2.name = "Айгерим", r2.age = 20, r2.group = "ИС-24-1";
MERGE (r3:Reader {id: 3}) SET r3.name = "Данияр", r3.age = 18, r3.group = "ИС-24-2";
MERGE (r4:Reader {id: 4}) SET r4.name = "Мадина", r4.age = 21, r4.group = "ИС-24-2";

MERGE (b1:Book {id: 101}) SET b1.title = "Преступление и наказание", b1.genre = "Роман", b1.year = 1866;
MERGE (b2:Book {id: 102}) SET b2.title = "Идиот", b2.genre = "Роман", b2.year = 1869;
MERGE (b3:Book {id: 103}) SET b3.title = "Мастер и Маргарита", b3.genre = "Фантастика", b3.year = 1967;
MERGE (b4:Book {id: 104}) SET b4.title = "Война и мир", b4.genre = "Исторический роман", b4.year = 1869;
MERGE (b5:Book {id: 105}) SET b5.title = "Анна Каренина", b5.genre = "Роман", b5.year = 1877;

MERGE (a1:Author {id: 201}) SET a1.name = "Фёдор Достоевский", a1.country = "Россия", a1.birthYear = 1821;
MERGE (a2:Author {id: 202}) SET a2.name = "Михаил Булгаков", a2.country = "Россия", a2.birthYear = 1891;
MERGE (a3:Author {id: 203}) SET a3.name = "Лев Толстой", a3.country = "Россия", a3.birthYear = 1828;
MERGE (a4:Author {id: 204}) SET a4.name = "Антон Чехов", a4.country = "Россия", a4.birthYear = 1860;

MATCH (r:Reader {id: 1}), (b:Book {id: 101}) MERGE (r)-[:BORROWED {date: "2026-09-10", status: "returned"}]->(b);
MATCH (r:Reader {id: 1}), (b:Book {id: 103}) MERGE (r)-[:BORROWED {date: "2026-10-02", status: "borrowed"}]->(b);
MATCH (r:Reader {id: 1}), (b:Book {id: 104}) MERGE (r)-[:BORROWED {date: "2026-10-12", status: "borrowed"}]->(b);
MATCH (r:Reader {id: 2}), (b:Book {id: 102}) MERGE (r)-[:BORROWED {date: "2026-09-15", status: "returned"}]->(b);
MATCH (r:Reader {id: 2}), (b:Book {id: 103}) MERGE (r)-[:BORROWED {date: "2026-10-05", status: "borrowed"}]->(b);
MATCH (r:Reader {id: 2}), (b:Book {id: 105}) MERGE (r)-[:BORROWED {date: "2026-10-18", status: "borrowed"}]->(b);
MATCH (r:Reader {id: 3}), (b:Book {id: 101}) MERGE (r)-[:BORROWED {date: "2026-08-20", status: "returned"}]->(b);
MATCH (r:Reader {id: 3}), (b:Book {id: 104}) MERGE (r)-[:BORROWED {date: "2026-10-01", status: "returned"}]->(b);
MATCH (r:Reader {id: 4}), (b:Book {id: 102}) MERGE (r)-[:BORROWED {date: "2026-10-11", status: "borrowed"}]->(b);
MATCH (r:Reader {id: 4}), (b:Book {id: 105}) MERGE (r)-[:BORROWED {date: "2026-10-20", status: "borrowed"}]->(b);

MATCH (a:Author {id: 201}), (b:Book {id: 101}) MERGE (a)-[:WROTE]->(b);
MATCH (a:Author {id: 201}), (b:Book {id: 102}) MERGE (a)-[:WROTE]->(b);
MATCH (a:Author {id: 202}), (b:Book {id: 103}) MERGE (a)-[:WROTE]->(b);
MATCH (a:Author {id: 203}), (b:Book {id: 104}) MERGE (a)-[:WROTE]->(b);
MATCH (a:Author {id: 203}), (b:Book {id: 105}) MERGE (a)-[:WROTE]->(b);

MATCH (r:Reader) RETURN r;

MATCH (r:Reader)
RETURN r.name AS reader, r.group AS groupName, r.age AS age
ORDER BY reader
LIMIT 10;

MATCH (r:Reader)-[rel:BORROWED]->(b:Book)
RETURN r.name AS reader, b.title AS book, rel.status AS status
ORDER BY reader, book;

MATCH (r:Reader)-[:BORROWED]->(b:Book {id: 103})
RETURN b.title AS book, r.name AS reader;

MATCH (r:Reader)-[:BORROWED]->(b:Book)<-[:WROTE]-(a:Author)
RETURN r.name AS reader, b.title AS book, a.name AS author
ORDER BY reader, book;

MATCH (r:Reader)
WHERE r.group = "ИС-24-1"
RETURN r.name AS reader, r.group AS groupName;

MATCH (b:Book)
WHERE b.year >= 1900
RETURN b.title AS book, b.year AS year
ORDER BY year;

MATCH (r:Reader)-[rel:BORROWED]->(b:Book)
WHERE rel.status = "borrowed"
RETURN r.name AS reader, b.title AS book, rel.date AS borrowDate
ORDER BY borrowDate;

MATCH (r:Reader {id: 1})
SET r.membership = "gold"
RETURN r;

MATCH (r:Reader {id: 1})-[rel:BORROWED]->(b:Book {id: 101})
SET rel.returnNote = "Возвращена без повреждений"
RETURN r.name AS reader, b.title AS book, rel.returnNote AS note;

MATCH (r1:Reader)-[:BORROWED]->(b:Book)<-[:BORROWED]-(r2:Reader)
WHERE r1.id < r2.id
RETURN r1.name AS reader1, r2.name AS reader2,
       collect(DISTINCT b.title) AS sharedBooks;

CREATE (:Temp {id: 999, note: "delete-me"});
MATCH (n:Temp {id: 999}) DETACH DELETE n;
MATCH (n:Temp {id: 999}) RETURN count(n) AS remaining;

MATCH (r:Reader) RETURN count(r) AS readers;
MATCH (b:Book) RETURN count(b) AS books;
MATCH (a:Author) RETURN count(a) AS authors;

MATCH ()-[rel]->() RETURN type(rel) AS relationshipType, count(rel) AS amount
ORDER BY relationshipType;

MATCH (n)
WITH labels(n) AS nodeLabels, n.id AS id, count(*) AS amount
WHERE id IS NOT NULL AND amount > 1
RETURN nodeLabels, id, amount;

