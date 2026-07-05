from django.db import models
from core.encryption import encrypt, decrypt


class EncryptedCharField(models.CharField):
    """CharField that transparently encrypts on write and decrypts on read.

    Important: do NOT override to_python here. CharField.get_prep_value calls
    self.to_python() internally, so overriding it would decrypt the plain-text
    value during save, corrupting it. from_db_value is sufficient for reads.
    """

    def from_db_value(self, value, expression, connection):
        return decrypt(value) if value else value

    def get_prep_value(self, value):
        # Skip super() — CharField.get_prep_value calls self.to_python() which
        # would try to decrypt plain text and return empty on failure.
        if not value:
            return value
        return encrypt(value)
