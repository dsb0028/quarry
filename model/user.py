from dataclasses import dataclass
from db import DB
from password import Password

# CREATE TABLE users (
# userid INTEGER PRIMARY KEY AUTOINCREMENT,
# username VARCHAR NOT NULL,
# password VARCHAR NOT NULL,
# email VARCHAR NOT NULL
# );

@dataclass
class User:
    """Hydrated user account."""
    userid: int
    username: str
    password: Password
    email: str

    def save(self, db: DB):
        assert(db.submit_query("SELECT userid FROM users WHERE userid = ?",
                               args=[self.userid],
                               one=True))
        db.execute_statements([("UPDATE users SET username = ?, password = password, email = ? WHERE userid = ?",
                                [username, password.serialize(), email, userid])])


def loaduser(db: DB, username: str) -> User:
    data = db.submit_query("SELECT * FROM users WHERE username = ?",
                           args=[username],
                           one=True)
    if data:
        return User(data["userid"], data["username"], Password(data["password"]), data["email"])
    else:
        return None

def createuser(db: DB, username: str, password: Password, email: str) -> User:
    return db.submit_query("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                           args=[username, password, email],
                           one=True)

if __name__ == "__main__":
    db = DB()
    print(createuser(db, "test1", "1234", "hello@email.com"))
    print(loaduser(db, "test1"))
