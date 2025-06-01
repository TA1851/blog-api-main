from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from uuid import uuid4
from database import Base

class EmailVerification(Base):
    """メール確認用のモデル"""
    __tablename__ = 'email_verifications'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    token = Column(String, unique=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    @classmethod
    def create_verification(cls, email: str):
        """新しい確認レコードを作成"""
        return cls(
            email=email,
            token=str(uuid4()),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
