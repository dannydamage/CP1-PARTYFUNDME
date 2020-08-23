import os
from unittest import TestCase
from sqlalchemy import exc
from .models import db, User


os.environ['DATABASE_URL'] = "postgresql:///partyfund-test"

"""Disable CSRF, initialize a  DB and seed a user"""


from partyfundme import app, bcrypt
from flask_login import current_user
from flask import request

db.create_all()

app.config["WTF_CSRF_ENABLED"] = False


class TestUser(TestCase):
    def setUp(self):
      
      """Create test client, add sample data."""
      db.drop_all()
      db.create_all()
      
      u1 = User(
                name="damage1", 
                email="damage1@me.com", 
                username="damage1", 
                password=(bcrypt.generate_password_hash("testyou")).decode('utf8')
              )
      uid1 = 1111
      u1.id = uid1

      u2 = User(
                name="damage2", 
                email="damage2@me.com", 
                username="damage2", 
                password=(bcrypt.generate_password_hash("testyou")).decode('utf8')
              )
      uid2 = 2222
      u2.id = uid2

      db.session.add(u1)
      db.session.add(u2)
      db.session.commit()

      self.u1 = u1
      self.uid1 = uid1

      self.u2 = u2
      self.uid2 = uid2

      self.client = app.test_client()

    def tearDown(self):
        """drop the db after each test"""
        db.drop_all()

    def test_user_registeration(self):
      """Ensure user can register"""
      with self.client:
            response = self.client.post('/signup', data=dict(
                username='tigarcia',password='moxie'
            ), follow_redirects=True)
            self.assertIn(b'You are logged in!', response.data)
            self.assertTrue(current_user.username == "tigarcia")
            # make sure we hash the password!
            self.assertNotEqual(current_user.password, "moxie")
            self.assertTrue(current_user.is_authenticated)

    def test_incorrect_user_registeration(self):
      """# Errors are thrown during an incorrect user registration"""
      with self.client:
            response = self.client.post('/signup', data=dict(
                username='eschoppik',password='doesnotmatter'))
            self.assertIn(b'Username already exists', response.data)
            self.assertIn('/signup', request.url)

    def test_get_by_id(self):
      """Ensure id is correct for the current/logged in user"""
      with self.client:
            self.client.post('/login', data=dict(
                username="admin", password='admin'
            ), follow_redirects=True)
            self.assertTrue(current_user.id == 1)
            self.assertFalse(current_user.id == 20)

    def test_check_password(self):
      """ Ensure given password is correct after unhashing """
      user = User.query.filter_by(username='admin').first()
      self.assertTrue(bcrypt.check_password_hash(user.password, 'admin'))
      self.assertFalse(bcrypt.check_password_hash(user.password, 'notadmin'))

    def test_login_page_loads(self):
      """Ensure that the login page loads correctly"""
      response = self.client.get('/login')
      self.assertIn(b'Please login', response.data)

    def test_correct_login(self):
      """User should be authenticated upon successful login and stored in current user"""
      with self.client:
            response = self.client.post(
                '/login',
                data=dict(username="eschoppik", password="secret"),
                follow_redirects=True
            )
            self.assertIn(b'Logged in!', response.data)
            self.assertTrue(current_user.username == "eschoppik")
            self.assertTrue(current_user.is_authenticated)

    def test_incorrect_login(self):
      """The correct flash message is sent when incorrect info is posted"""
      response = self.client.post(
            '/login',
            data=dict(username="dsadsa", password="dsadsadsa"),
            follow_redirects=True
        )
      self.assertIn(b'Invalid Credentials', response.data)

    def test_logout(self):
      """Make sure log out actually logs out a user"""
      with self.client:
            self.client.post(
                '/login',
                data=dict(username="eschoppik", password="secret"),
                follow_redirects=True
            )
            response = self.client.get('/logout', follow_redirects=True)
            self.assertIn(b'You are logged out!', response.data)
            self.assertFalse(current_user.is_authenticated)

    def test_logout_route_requires_login(self):
      """Make sure that you can not log out without being logged in"""
      response = self.client.get('/logout', follow_redirects=True)
      self.assertIn(b'Please log in to access this page', response.data)