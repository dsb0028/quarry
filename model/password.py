import argon2
from dataclasses import dataclass

ph = argon2.PasswordHasher(time_cost=5,
                           memory_cost=409600,
                           hash_len=32,
                           salt_len=32)

@dataclass
class Password:
    _pwhash: str

    def create(password: str):
        return Password(ph.hash(password))

    def verify(self, password: str) -> bool:
        try:
            return ph.verify(self._pwhash, password)
        except VerificationError:
            return False

    def serialize(self):
        return self._pwhash
        
