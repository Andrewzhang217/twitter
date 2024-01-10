from friendships.api.paginations import FriendshipPagination
from friendships.models import Friendship
from friendships.services import FriendshipService
from rest_framework.test import APIClient
from testing.testcases import TestCase

FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        super(FriendshipApiTests, self).setUp()
        self.t_user1 = self.create_user('t_user1')
        self.t_user1_client = APIClient()
        self.t_user1_client.force_authenticate(self.t_user1)

        self.t_user2 = self.create_user('t_user2')
        self.t_user2_client = APIClient()
        self.t_user2_client.force_authenticate(self.t_user2)

        # create followings and followers for t_user2
        for i in range(2):
            follower = self.create_user('t_user2_follower{}'.format(i))
            self.create_friendship(from_user=follower, to_user=self.t_user2)
        for i in range(3):
            following = self.create_user('t_user2_following{}'.format(i))
            self.create_friendship(from_user=self.t_user2, to_user=following)

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
        before_count = FriendshipService.get_following_count(self.t_user1.id)
        response = self.t_user1_client.post(FOLLOW_URL.format(self.t_user2.id))
        self.assertEqual(response.status_code, 201)
        after_count = FriendshipService.get_following_count(self.t_user1.id)
        self.assertEqual(after_count, before_count + 1)

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
        self.create_friendship(from_user=self.t_user2, to_user=self.t_user1)
        before_count = FriendshipService.get_following_count(self.t_user2.id)
        response = self.t_user2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        after_count = FriendshipService.get_following_count(self.t_user2.id)
        self.assertEqual(after_count, before_count - 1)

        # if not followed, silent unfollow request
        before_count = FriendshipService.get_following_count(self.t_user2.id)
        response = self.t_user2_client.post(url)
        after_count = FriendshipService.get_following_count(self.t_user2.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(after_count, before_count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.t_user2.id)
        # POST is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # GET is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        # ensure ordered by -created_at
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            't_user2_following2',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            't_user2_following1',
        )
        self.assertEqual(
            response.data['results'][2]['user']['username'],
            't_user2_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.t_user2.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        print(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # ensure ordered by -created_at
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            't_user2_follower1',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            't_user2_follower0',
        )

    def test_followers_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            follower = self.create_user('t_user1_follower{}'.format(i))
            self.create_friendship(from_user=follower, to_user=self.t_user1)
            if follower.id % 2 == 0:
                self.create_friendship(from_user=self.t_user2, to_user=follower)

        url = FOLLOWERS_URL.format(self.t_user1.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # t_user2 has followed users with even id
        response = self.t_user2_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            following = self.create_user('t_user1_following{}'.format(i))
            self.create_friendship(from_user=self.t_user1, to_user=following)
            if following.id % 2 == 0:
                self.create_friendship(from_user=self.t_user2, to_user=following)

        url = FOLLOWINGS_URL.format(self.t_user1.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # t_user2 has followed users with even id
        response = self.t_user2_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        # t_user1 has followed all his following users
        response = self.t_user1_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

    def _test_friendship_pagination(self, url, page_size, max_page_size):
        response = self.anonymous_client.get(url, {'page': 1})
        # print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        response = self.anonymous_client.get(url, {'page': 2})
        # print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 2)
        self.assertEqual(response.data['has_next_page'], False)

        response = self.anonymous_client.get(url, {'page': 3})
        self.assertEqual(response.status_code, 404)

        # test user can not customize page_size which exceeds max_page_size
        response = self.anonymous_client.get(url, {'page': 1, 'size': max_page_size + 1})
        self.assertEqual(len(response.data['results']), max_page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        # test user can customize page size by param size
        response = self.anonymous_client.get(url, {'page': 1, 'size': 2})
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['total_pages'], page_size)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)
