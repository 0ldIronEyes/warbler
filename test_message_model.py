"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes



os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.uid = 1
        u = User.signup("testing", "testing@test.com", "password", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""
        
        m = Message(text="message",user_id=self.uid)
        db.session.add(m)
        db.session.commit

        self.assertIsNotNone(m)
        self.assertEqual(self.u.messages[0].text,"message")
        self.assertEqual(m.user_id,1)

    def test_likes(self):
        """test likes"""
        message = Message(text="message",user_id=self.uid)
        db.session.add(message)
        db.session.commit

        secondUser= User.signu("new","testing@testing.com","password",None)
        secondUser.id= 11
        secondUser.likes.append(message)
        db.session.add(secondUser)
        db.session.commit()

        like = Likes.query.filter_by(user_id=11)
        self.assertIsNotNone(like)
        


