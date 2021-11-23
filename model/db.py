import os, sqlite3, contextlib

class DB:
    filename = "model.db"
    schema = """
BEGIN;
CREATE TABLE users (
userid INTEGER PRIMARY KEY AUTOINCREMENT,
username VARCHAR NOT NULL UNIQUE,
password VARCHAR NOT NULL,
email VARCHAR NOT NULL
);

CREATE TABLE notes (
noteid INTEGER PRIMARY KEY AUTOINCREMENT,
author INTEGER NOT NULL,
text VARCHAR NOT NULL,
FOREIGN KEY (author) REFERENCES users(userid)
);

CREATE TABLE tags (
tagid INTEGER PRIMARY KEY AUTOINCREMENT,
text VARCHAR NOT NULL
);

CREATE TABLE join_notes_tags (
noteid INTEGER NOT NULL,
tagid INTEGER NOT NULL,

FOREIGN KEY (noteid) REFERENCES notes(noteid),
FOREIGN KEY (tagid) REFERENCES tags(tagid)
);

CREATE TABLE cards (
cardid INTEGER PRIMARY KEY AUTOINCREMENT,
noteid INTEGER NOT NULL,
nextreview VARCHAR,
interval REAL CHECK (interval > 0),
ease REAL CHECK (ease > 1),

FOREIGN KEY (noteid) REFERENCES notes(noteid)
);

CREATE TABLE reviews (
cardid INTEGER NOT NULL,
userid INTEGER NOT NULL,
reviewcount INTEGER NOT NULL CHECK (reviewcount >= 0),
interval REAL NOT NULL CHECK (interval > 0),
interval_deviation REAL DEFAULT 0.0,

FOREIGN KEY (cardid) REFERENCES cards(cardid),
FOREIGN KEY (userid) REFERENCES users(userid),
PRIMARY KEY (userid, cardid, reviewcount)
);

COMMIT;
"""
    def __init__(self):
        if not (os.path.exists(DB.filename) and os.path.isfile(DB.filename)):
            with contextlib.closing(sqlite3.connect(DB.filename)) as db:
                db.cursor().executescript(DB.schema)

        self._connection = sqlite3.connect(DB.filename)

    def __del__(self):
        self._connection.close()

    # https://flask-doc.readthedocs.io/en/latest/patterns/sqlite3.html
    def submit_query(self, query: str, args=(), one=False):
        """Wrapper for queries which returns results intelligently."""
        assert(query.split()[0] == "SELECT",
               "Use execute_statement for Data Modification Language statements. (anything that isn't select)")
        cur = self._connection.execute(query, args)
        rv = [dict((cur.description[idx][0], value)
                   for idx, value in enumerate(row))
              for row in cur.fetchall()]

        return (rv[0] if rv else None) if one else rv

    # https://stackoverflow.com/a/44448465
    def execute_statements(self, statements):
        """Execute a series of statements within a single transaction."""
        with self._connection as conn:
            conn.execute("BEGIN")
            for statement in satements:
                if isinstance(statement, (tuple, list)):
                    template, args = statement
                    conn.execute(template, args)
                else:
                    assert(isinstance(statement, str))
                    conn.execute(statement)

    def execute_statement(self, statement, args=()):
        """Execute a single statement."""
        self.execute_statements([(statement, args)])

    def commit(self):
        self._connection.commit()