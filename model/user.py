from dataclasses import dataclass
from db import DB
from password import Password

# CREATE TABLE users (
# userid INTEGER PRIMARY KEY AUTOINCREMENT,
# username VARCHAR NOT NULL UNIQUE,
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
        db.execute_statement("UPDATE users SET username = ?, password = password, email = ? WHERE userid = ?",
                             [username, password.serialize(), email, userid])

    def hydrate(db: DB, userid: int):
        data = db.submit_query("SELECT * FROM users WHERE userid = ?",
                               args=[userid],
                               one=True)
        if data:
            return User(data["userid"], data["username"], Password(data["password"]), data["email"])
        else:
            return None

    def create(db: DB, username: str, password: str, email: str):
        password = Password.create(password)
        key = db.nextkey("users")
        db.execute_statement("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                             [username, password.serialize(), email])
        user = User.hydrate(db, key)
        if not user:
            user = User.load(db, username)

        return user

    def load(db: DB, username: str):
        data = db.submit_query("SELECT * FROM users WHERE username = ?",
                               args=[username],
                               one=True)
        if data:
            return User(data["userid"], data["username"], Password(data["password"]), data["email"])
        else:
            return None

if __name__ == "__main__":
    db = DB()
    print(User.create(db, "test1", "1234", "hello@email.com"))
    print(User.load(db, "test1"))
    u = User.create(db, "test2", "1234", "hiii@email.com")
    u.email = "goodbye"
    u.save(db)
    print(User.load(db, "test2"))
