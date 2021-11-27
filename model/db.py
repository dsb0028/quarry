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
notetype VARCHAR NOT NULL,
FOREIGN KEY (author) REFERENCES users(userid)
);

CREATE TABLE tags (
tagid INTEGER PRIMARY KEY AUTOINCREMENT,
text VARCHAR NOT NULL UNIQUE
);

CREATE TABLE join_notes_tags (
noteid INTEGER NOT NULL,
tagid INTEGER NOT NULL,

FOREIGN KEY (noteid) REFERENCES notes(noteid),
FOREIGN KEY (tagid) REFERENCES tags(tagid),
PRIMARY KEY (noteid, tagid)
);

CREATE TABLE cards (
cardid INTEGER PRIMARY KEY AUTOINCREMENT,
noteid INTEGER NOT NULL,
userid INTEGER NOT NULL,
template VARCHAR NOT NULL,
due VARCHAR NOT NULL,
ease REAL NOT NULL CHECK (ease > 1),
interval INTEGER CHECK (interval > 0),

FOREIGN KEY (userid) REFERENCES users(userid),
FOREIGN KEY (noteid) REFERENCES notes(noteid)
);

CREATE TABLE reviews (
reviewid INTEGER PRIMARY KEY AUTOINCREMENT,
cardid INTEGER NOT NULL,
due VARCHAR,
date VARCHAR NOT NULL,
ease REAL NOT NULL,
score REAL NOT NULL CHECK (score >= 0.0 AND score <= 1.0),

FOREIGN KEY (cardid) REFERENCES cards(cardid)
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
               "Use execute_statement(s) for Data Modification Language statements. (anything that isn't select)")
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
            for statement in statements:
                if isinstance(statement, tuple):
                    template, args = statement
                    conn.execute(template, args)
                else:
                    assert(isinstance(statement, str), "Invalid type: {}".format(type(statement)))
                    conn.execute(statement)

    def execute_statement(self, statement, args=()):
        """Execute a single statement."""
        self.execute_statements([(statement, args)])

    def nextkey(self, tablename: str) -> int:
        """Obtain the next primary key to be generated in the given table."""
        """Assumes the table uses an integer autoincrement primary key."""
        cursor = self._connection.execute("SELECT seq FROM sqlite_sequence WHERE name = ?",
                                          [tablename])
        row = cursor.fetchone()
        if row:
            # https://sqlite.org/autoinc.html
            # This could fail but I can't think how else to do this.
            # TODO: Find a better solution.
            return row[0] + 1
        else:
            return 1
        

    def commit(self):
        self._connection.commit()
