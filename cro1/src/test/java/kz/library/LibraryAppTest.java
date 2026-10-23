package kz.library;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class LibraryAppTest {
    static LibraryApp app;
    @BeforeAll static void setup() {
        app = new LibraryApp("mongodb://localhost:27017", "library_nosql_test");
        app.createIndexes();
        app.seedData();
    }
    @AfterAll static void cleanup() { app.close(); }
    @Test void seedCreatesExpectedCounts() {
        assertEquals(30, app.countBooks());
        assertEquals(15, app.countReaders());
        assertEquals(45, app.countLoans());
    }
    @Test void unknownBookCannotBeIssued() {
        assertThrows(IllegalArgumentException.class, () -> app.issueBook("MISSING", "R001"));
    }
    @Test void bookSearchReturnsList() {
        assertNotNull(app.findBooks("робот"));
    }
}
