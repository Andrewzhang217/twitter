from friendships.models import Friendship
from rest_framework.test import APIClient
from testing.testcases import TestCase

FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.t_user1 = self.create_user('t_user1')
        self.t_user1_client = APIClient()
        self.t_user1_client.force_authenticate(self.t_user1)

        self.t_user2 = self.create_user('t_user2')
        self.t_user2_client = APIClient()
        self.t_user2_client.force_authenticate(self.t_user2)

        # create followings and followers for t_user2
        for i in range(2):
            follower = self.create_user('t_user2_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.t_user2)
        for i in range(3):
            following = self.create_user('t_user2_following{}'.format(i))
            Friendship.objects.create(from_user=self.t_user2, to_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.t_user1.id)
        # logged in to follow
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # GET not allowed for follow
        response = self.t_user2_client.get(url)
        self.assertEqual(response.status_code, 405)
        # not allowed to follow yourself
        response = self.t_user1_client.post(url)
        self.assertEqual(response.status_code, 400)
        # follow OK
        response = self.t_user2_client.post(url)
        self.assertEqual(response.status_code, 201)
        # duplicate follow 400
        response = self.t_user2_client.post(url)
        self.assertEqual(response.status_code, 400)
        # reverse follow will create new data
        count = Friendship.objects.count()
        response = self.t_user1_client.post(FOLLOW_URL.format(self.t_user2.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.t_user1.id)

        # logged in to follow
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # GET not allowed for follow
        response = self.t_user2_client.get(url)
        self.assertEqual(response.status_code, 405)
        # not allowed to unfollow yourself
        response = self.t_user1_client.post(url)
        self.assertEqual(response.status_code, 400)
        # unfollow OK
        Friendship.objects.create(from_user=self.t_user2, to_user=self.t_user1)
        count = Friendship.objects.count()
        response = self.t_user2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)
        # if not followed, silent unfollow request
        count = Friendship.objects.count()
        response = self.t_user2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.t_user2.id)
        # POST is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # GET is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)
        # ensure ordered by -created_at
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            't_user2_following2',
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            't_user2_following1',
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            't_user2_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.t_user2.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)
        # ensure ordered by -created_at
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            't_user2_follower1',
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            't_user2_follower0',
        )
