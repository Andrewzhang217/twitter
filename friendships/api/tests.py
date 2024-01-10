from friendships.api.paginations import FriendshipPagination
from friendships.services import FriendshipService
from rest_framework.test import APIClient
from testing.testcases import TestCase
from utils.paginations import EndlessPagination

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
        print(response.data)
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
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            follower = self.create_user('t_user1_follower{}'.format(i))
            friendship = self.create_friendship(from_user=follower, to_user=self.t_user1)
            friendships.append(friendship)
            if follower.id % 2 == 0:
                self.create_friendship(from_user=self.t_user2, to_user=follower)

        url = FOLLOWERS_URL.format(self.t_user1.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # t_user2 has followed users with even id
        response = self.t_user2_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            following = self.create_user('t_user1_following{}'.format(i))
            f = self.create_friendship(from_user=self.t_user1, to_user=following)
            friendships.append(f)
            if following.id % 2 == 0:
                self.create_friendship(from_user=self.t_user2, to_user=following)

        url = FOLLOWINGS_URL.format(self.t_user1.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # t_user2 has followed users with even id
        response = self.t_user2_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        # t_user1 has followed all his following users
        response = self.t_user1_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

        # test pull new friendships
        last_created_at = friendships[-1].created_at
        response = self.t_user1_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        new_friends = [self.create_user('KOL_{}'.format(i)) for i in range(3)]
        new_friendships = []
        for friend in new_friends:
            new_friendships.append(self.create_friendship(from_user=self.t_user1, to_user=friend))
        response = self.t_user1_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(len(response.data['results']), 3)
        for result, friendship in zip(response.data['results'], reversed(new_friendships)):
            self.assertEqual(result['created_at'], friendship.created_at)

    def _paginate_until_the_end(self, url, expect_pages, friendships):
        results, pages = [], 0
        response = self.anonymous_client.get(url)
        results.extend(response.data['results'])
        pages += 1
        while response.data['has_next_page']:
            self.assertEqual(response.status_code, 200)
            last_item = response.data['results'][-1]
            response = self.anonymous_client.get(url, {
                'created_at__lt': last_item['created_at'],
            })
            results.extend(response.data['results'])
            pages += 1

        self.assertEqual(len(results), len(friendships))
        self.assertEqual(pages, expect_pages)
        # friendship is in ascending order, results is in descending order
        for result, friendship in zip(results, friendships[::-1]):
            self.assertEqual(result['created_at'], friendship.created_at)
