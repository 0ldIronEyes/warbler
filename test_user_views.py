"""User View tests."""


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"




from app import app, CURR_USER_KEY


db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuserA = User.signup(username="test", email="email@test.com", password="pass",image_url=None)
        self.testuserA.id = 22
        self.testuserB = User.signup(username="user", email= "email@user.com", password= "worddd", image_url=None)
        self.testuserB.id = 33
        self.testuserC = User.signup(username="testC", email= "testemail@user.com", password="password", image_url=None)
        self.testuserC.id = 44
        db.session.commit()

    
    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp
    
    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@test", str(resp.data))
            self.assertIn("@user", str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuserA.id}")

            self.assertIn("@test", str(resp.data))

    def test_user_with_likes(self):
        
        with self.client as c:
            m1 = Message(text="messaggge", user_id=self.testuserA.id)
            m2 = Message(id=9876, text="another message", user_id=self.testuserA.id)
            db.session.add_all([m1, m2])
            db.session.commit()
            l1 = Likes(user_id=self.testuserA.id, message_id=9876)

            db.session.add(l1)
            db.session.commit()

            resp = c.get(f"/users/{self.testuserA.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            self.assertIn("2", found[0].text)

            self.assertIn("0", found[1].text)

            self.assertIn("0", found[2].text)

            self.assertIn("1", found[3].text)

    
    def test_add_like(self):
        m = Message(id=1984, text="blllaaa", user_id=self.testuserA.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuserA.id

            resp = c.post("/messages/1984/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == 1984).one()
            self.assertEqual(likes[0].user_id,self.testuserA)

    def test_remove_like(self):
        m1 = Message(text="messaggge", user_id=self.testuserA.id)
        m2 = Message(id=9876, text="another message", user_id=self.testuserA.id)
        db.session.add_all([m1, m2])
        db.session.commit()
        l1 = Likes(user_id=self.testuserA.id, message_id=9876)

        db.session.add(l1)
        db.session.commit()

        m= Message.query.filter(Message.text=="another message").one()
        self.assertIsNotNone(m)

        l = Likes.query.filter(Likes.user_id==self.testuserA.id and Likes.message_id== m.id).one()
        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuserA.id

            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)

    
    def test_unauthenticated_like(self):
        m1 = Message(text="messaggge", user_id=self.testuserA.id)
        m2 = Message(id=9876, text="another message", user_id=self.testuserA.id)
        db.session.add_all([m1, m2])
        db.session.commit()
        l1 = Likes(user_id=self.testuserA.id, message_id=9876)

        db.session.add(l1)
        db.session.commit()
        m = Message.query.filter(Message.text=="another message").one()
        self.assertIsNotNone(m)
        like_count = Likes.query.count()
        with self.client as c:
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            self.assertEqual(like_count, Likes.query.count())

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.testuserB.id, user_following_id=self.testuserA.id)
        f2 = Follows(user_being_followed_id=self.testuserC, user_following_id=self.testuserA.id)
        f3 = Follows(user_being_followed_id=self.testuserA.id, user_following_id=self.testuserB.id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()    

    def test_user_show_with_follows(self):

        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuserA.id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            self.assertIn("0", found[0].text)

            self.assertIn("2", found[1].text)



    def test_show_following(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuserA.id

            resp = c.get(f"/users/{self.testuserA.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test", str(resp.data))
            self.assertIn("@user", str(resp.data))
            self.assertNotIn("@blue", str(resp.data))

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:
            resp = c.get(f"/users/{self.testuserA.id}/following", follow_redirects= True)
            self.assertIn("Access unauthorized", str(resp.data))
    
    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:
            resp = c.get(f"/users/{self.testuserA.id}/followers", follow_redirects= True)
            self.assertIn("Access unauthorized", str(resp.data))