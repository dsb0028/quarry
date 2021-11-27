from dataclasses import dataclass
from datetime import date, timedelta
from db import DB
from note import Note
from user import User

# CREATE TABLE reviews (
# reviewid INTEGER PRIMARY KEY AUTOINCREMENT,
# cardid INTEGER NOT NULL,
# due VARCHAR,
# date VARCHAR,
# score REAL NOT NULL CHECK (score >= 0.0 AND score <= 1.0),

# FOREIGN KEY (cardid) REFERENCES cards(cardid)
# );

@dataclass
class Card:
    """The unit of memorization."""
    cardid: int
    parent: Note
    user: User
    template: str
    due: date
    ease: float
    interval: timedelta

    def save(self, db: DB):
        assert(db.submit_query("SELECT cardid FROM cards WHERE cardid = ?",
                               args=[self.cardid],
                               one=True))
        db.execute_statement("UPDATE cards SET noteid = ?, userid = ?, template = ?, due = ?, ease = ?, interval = ? WHERE cardid = ?",
                             [self.parent.noteid,
                              self.user.userid,
                              self.template,
                              self.due.isoformat(),
                              self.ease,
                              self.interval.days,
                              self.cardid])

    def hydrate(db: DB, cardid: int):
        data = db.submit_query("SELECT * FROM cards WHERE cardid = ?",
                               args=[cardid],
                               one=True)
        if data:
            return Card(data["cardid"],
                        Note.hydrate(db, data["noteid"]),
                        User.hydrate(db, data["userid"]),
                        data["template"],
                        date.fromisoformat(data["due"]),
                        data["ease"],
                        timedelta(days=data["interval"]))
        else:
            return None

    def create(db: DB, parent: Note, user: User, template: str):
        key = db.nextkey("cards")
        due = date.today()
        interval = timedelta(days=1)
        ease = 1.5
        db.execute_statement("INSERT INTO cards (noteid, userid, template, due, ease, interval) VALUES (?, ?, ?, ?, ?, ?)",
                             [parent.noteid, user.userid, template, due.isoformat(), ease, interval.days])
        return Card.hydrate(db, key)

    def review(self, db: DB, score: float):
        """Record a new review of this card, and reschedule appropriately."""
        assert(0.0 <= score and score <= 1.0)
        reviews = db.submit_query("SELECT ease, score FROM reviews WHERE cardid = ? ORDER BY date DESC",
                                  args=[self.parent.noteid])

        # Compute average ease/score
        if reviews:
            # TODO: Check for leeches.
            from functools import reduce
            reviews.append({"ease": self.ease, "score": score})
            numreviews = len(reviews)
            if numreviews > 10:
                reviews = reviews[numreviews - 10:]
                numreviews = 10
            totalease, totalscore = reduce(lambda runningsum, review: (review["ease"] + runningsum[0],
                                                                       review["score"] + runningsum[1]),
                                           reviews,
                                           (0, 0))
            avgease = totalease / numreviews
            avgscore = totalscore / numreviews
        else:
            avgease = self.ease
            avgscore = score

        # Recalculate ease:
        # H/T: https://eshapard.github.io/anki/thoughts-on-a-new-algorithm-for-anki.html
        from math import log
        avgscore = max(avgscore, 0.01)
        avgscore = min(avgscore, 0.99)
        adjustedease = avgease * log(.85) / log(avgscore)

        # Cap the adjustment to +/- 20%
        if adjustedease > self.ease:
            newease = min(adjustedease, self.ease * 1.2)
        else:
            newease = max(adjustedease, self.ease * 0.8)

        # Impose sensible bounds on newease.
        newease = max(1.3, newease)
        newease = min(2.5, newease)

        # Shrink interval if score indicates forgottenness.
        if score <= 0.1:
            newinterval = self.interval / (3.5 - newease)
        else:
            newinterval = self.interval * newease
            # Add a day to get out of low ease 1-day ruts
            if newinterval < timedelta(days=10):
                newinterval += timedelta(days=1)

        # Impose sensible bounds on newinterval.
        newinterval = max(timedelta(days=1), newinterval)
        newinterval = min(timedelta(days=3*365), newinterval) # I can maybe relax this?

        # Record review
        db.execute_statement("INSERT INTO reviews (cardid, due, date, ease, score) VALUES (?, ?, ?, ?, ?)",
                             args=[self.cardid, self.due, date.today().isoformat(), self.ease, score])

        # Reschedule
        self.ease = newease
        self.interval = newinterval
        self.due = date.today() + self.interval
        self.save(db)
        return self.due

    def fetchbyparent(db: DB, parent: Note):
        data = db.submit_query("SELECT cardid FROM cards WHERE noteid = ?",
                               args=[self.parent.noteid])
        return list(map(lambda datum: Card.hydrate(db, datum["cardid"]),
                        data))


if __name__ == "__main__":
    db = DB()
    user = User.load(db, "testnoteauthor")
    if not user:
        user = User.create(db, "testnoteauthor", "aaaa", "email")
    note = Note.create(db, user, "Card: The unit of memorization.")
    card = Card.create(db, note, user, "Test card")
    print(card)
    for _ in range(3):
        for _ in range(3):
            i = 1.0
            print(i, card.review(db, i) - date.today(), card.ease)
        for _ in range(2):
            i = 0.0
            print(i, card.review(db, i) - date.today(), card.ease)
    for _ in range(2):
        for _ in range(9):
            i = 1.0
            print(i, card.review(db, i) - date.today(), card.ease)
        for _ in range(1):
            i = 0.0
            print(i, card.review(db, i) - date.today(), card.ease)
