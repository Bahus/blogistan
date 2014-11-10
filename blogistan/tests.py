# -*- coding: utf-8 -*-
import unittest
import transaction

from pyramid import testing
from sqlalchemy import create_engine

from blogistan.models import DBSession, Base, User, Post, PostViewCount


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.engine = create_engine('sqlite://')
        DBSession.configure(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)
        self.session = DBSession()

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()


class TestSomeServerSideLogic(BaseTest):

    def setUp(self):
        super(TestSomeServerSideLogic, self).setUp()
        self.user = User(name='bahusoff')
        self.post = Post(author=self.user, body='test body')

        with transaction.manager:
            self.session.add_all([self.user, self.post])

    def test_posts_list(self):
        user = User(name='admin')
        post1 = Post(author=user, body='Hello, world!')
        post2 = Post(author=user, body=u'Привет, мир!')
        view_count = PostViewCount(count=10, post=post1)

        with transaction.manager:
            self.session.add_all([post1, post2, view_count])

        post_data = Post.get_list()
        self.assertEqual(len(post_data), 3)

        self.assertItemsEqual(
            [d['post_body'] for d in post_data],
            [self.post.body, post1.body, post2.body]
        )

        self.assertItemsEqual(
            set(d['username'] for d in post_data),
            {self.user.name, user.name}
        )

        self.assertItemsEqual(
            [d['view_count'] for d in post_data],
            [10, 1, 1],
        )

    def test_counter_increment(self):
        counter = self.post.create_or_increment_counter(commit=True)
        self.assertEqual(counter.count, 1)

        counter = self.post.create_or_increment_counter(commit=True)
        self.assertEqual(counter.count, 2)
