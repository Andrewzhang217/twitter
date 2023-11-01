from testing.testcases import TestCase
from rest_framework.test import APIClient

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'


class AccountApiTests(TestCase):

    def setUp(self):
        # executed in every test function
        self.client = APIClient()
        self.user = self.create_user(
            username="admin",
            email="admin@gmail.com",
            password='correctPassword',
        )

    def test_login(self):
        # test GET method, should always use POST method
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correctPassword',
        })

        # return 405 = METHOD_NOT_ALLOWED
        self.assertEqual(response.status_code, 405)

        # test POST with wrong password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrongPassword',
        })
        self.assertEqual(response.status_code, 400)

        # test not logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # test login with correct password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correctPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'admin@gmail.com')
        self.assertEqual(response.data['user']['username'], 'admin')

        # test login status after successful login
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # login first
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correctPassword',
        })

        # test successful login
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # test GET method, must use POST
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # test successful logout with POST method
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        # test login status after logout
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@gmail.com',
            'password': 'anyPassword',
        }

        # test GET method, must use POST
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # test invalid email address
        response = self.client.post(SIGNUP_URL, {
            'username': "someone",
            'email': 'not a valid email',
            'password': 'anyPassword',
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # test too short password
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@gmail.com',
            'password': '123',
        })
        print(response.data)
        self.assertEqual(response.status_code, 400)

        # test too long username
        response = self.client.post(SIGNUP_URL, {
            'username': 'this user name is really too long',
            'email': 'someone@gmail.com',
            'password': 'anyPassword',
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # test a successful signup
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')

        # test login status
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)
