from dataclasses import dataclass
from db import DB
from user import User

# CREATE TABLE notes (
# noteid INTEGER PRIMARY KEY AUTOINCREMENT,
# author INTEGER NOT NULL,
# text VARCHAR NOT NULL,
# notetype VARCHAR NOT NULL,
# FOREIGN KEY (author) REFERENCES users(userid)
# );

@dataclass
class Note:
    """The unit of authorship."""
    noteid: int
    author: User
    text: str
    notetype: str

    def save(self, db: DB):
        assert(db.submit_query("SELECT noteid FROM notes WHERE noteid = ?",
                               args=[self.noteid],
                               one=True))
        db.execute_statement("UPDATE notes SET author = ?, text = ?, notetype = ? WHERE noteid = ?",
                             [self.author.userid, self.text, self.notetype, self.noteid])

    def hydrate(db: DB, noteid: int):
        data = db.submit_query("SELECT * FROM notes WHERE noteid = ?",
                               args=[noteid],
                               one=True)
        if data:
            return Note(data["noteid"], User.hydrate(db, data["author"]), data["text"], data["notetype"])
        else:
            return None

    def create(db: DB, author: User, text: str, notetype: str = "yaml"):
        key = db.nextkey("notes")
        db.execute_statement("INSERT INTO notes (author, text, notetype) VALUES (?, ?, ?)",
                             [author.userid, text, notetype])
        return Note.hydrate(db, key)

    def fetchbyauthor(db: DB, author: User):
        data = db.submit_query("SELECT noteid FROM notes WHERE author = ?",
                               args=[author.userid])
        return list(map(lambda datum: Note.hydrate(db, datum["noteid"]),
                        data))

if __name__ == "__main__":
    db = DB()
    user = User.load(db, "testnoteauthor")
    if not user:
        user = User.create(db, "testnoteauthor", "aaaa", "email")
    note = Note.create(db, user, "this is a note")
    print(note)
    note.text = "this is the same note"
    note.save(db)
    print(Note.hydrate(db, note.noteid))
    Note.create(db, user, "this is a different note")
    print(Note.fetchbyauthor(db, user))
