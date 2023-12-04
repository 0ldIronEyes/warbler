"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

       

        user1 = User.signup("test1", "test1@email.com", "testpass", None)
        user1.id = 1
        self.user1 = user1
        user2 = User.signup("test2", "test2@email.com","testpass",None)
        self.user2 = 2
        self.user2= user2
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    def test_user_not_following(self):
        self.user1.following.clear
        db.session.commit()
        self.assertFalse(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_following(self.user2))


    def test_user_follow_count(self):
        self.user1.following.append(self.user2)
        db.session.commit()
        self.AssertEqual(self.user1.following[0].id,self.user2.id)
        self.AssertEqual(self.user2.followers[0].id, self.user1.id)

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()
        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        self.user2.following.append(self.user1)
        db.session.commit()
        self.assertTrue(self.user1.is_followed_by(self.user2))
        self.assertFalse(self.user2.is_followed_by(self.user1))

    def test_user_creation(self):
        testuser = User.signup("tuser","tuser@user.com","pass",None)
        testuser.id =3
        db.session.commit()
        self.assertIsNotNone(User.query.get(testuser.id))
        self.assertEqual(User.query.get(testuser.id).username, "tuser")
        self.assertFalse(User.query.get(testuser.id).password, "pass")


    def test_invalid_username_creation(self):
        testuser = User.signup("test1","tuser@user.com","passs",None)
        tid = 122
        testuser.id = tid
        db.session.commit()
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_creation(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", None, None)

    def test_valid_authenticate(self):
        user = User.authenticate(self.user1.username, "testpass")
        self.assertIsNotNone(user)

    def test_invalid_username(self):
        user =  User.authenticate("tttttt", "testpass")
        self.assertFalse(user)

    def test_invalid_password(self):
        user =  User.authenticate(self.user1.username, "1")
        self.assertFalse(user)