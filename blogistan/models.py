# -*- coding: utf-8 -*-
import transaction
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey, desc)

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    joinedload)

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(
    sessionmaker(extension=ZopeTransactionExtension(),
                 expire_on_commit=False),  # TODO: это ок?
)

Base = declarative_base()


class User(Base):
    """Пользователь, который может написать пост"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    posts = relationship('Post', backref='author')

    def __repr__(self):
        return u'<User(name={})>'.format(self.name)


class Post(Base):
    """Пост, который может написать пользователь"""
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    body = Column(Text)
    author_id = Column(Integer, ForeignKey('users.id'))
    view_count = relationship('PostViewCount', uselist=False, backref='post')

    PER_PAGE_COUNT = 30  # максильмальное количество постов на главной

    @classmethod
    def get_list(cls):
        posts = (
            DBSession().query(cls)
                       .options(joinedload('author'))
                       .options(joinedload('view_count'))
                       .order_by(desc(cls.id))
                       .all()
        )[:cls.PER_PAGE_COUNT]
        return posts

    @classmethod
    def get_data_list(cls, update_counters=False):
        posts_data = []

        with transaction.manager:

            for post in cls.get_list():

                post_data = {
                    'post_body': post.body,
                    'username': post.author.name,
                    'view_count': (post.view_count.count
                                   if post.view_count else 1)
                }

                if update_counters:
                    # При увеличении счетчиков просмотра не требуется
                    # оптимизировать код для пакетного обновления, можно
                    # увеличивать их по одному.
                    counter = post.create_or_increment_counter()
                    post_data['view_count'] = counter.count

                posts_data.append(post_data)

        return posts_data

    def create_or_increment_counter(self):
        """Создаем запись в просмотрах поста, если ее нет,
        а если есть, то атомарно увеличиваем на 1
        """
        session = DBSession()

        if self.view_count is not None:
            self.view_count.count = PostViewCount.count + 1
            session.add(self.view_count)
            session.flush()
            # TODO: здесь можно сэкономить запрос, просто добавив
            # 1 к текущему значению, оно будет менее точно, но это не
            # принципиально
            session.refresh(self.view_count)
        else:
            self.view_count = PostViewCount(post=self)
            session.add(self.view_count)
            session.flush()

        return self.view_count

    def __repr__(self):
        return u'<Post(id={}, author={})>'.format(self.id, self.author.name)


class PostViewCount(Base):
    """Счетчики просмотров для каждого поста"""
    __tablename__ = 'post_view_counts'
    count = Column(Integer, default=1)
    post_id = Column(
        Integer,
        ForeignKey('posts.id'),
        primary_key=True,
    )

    def __repr__(self):
        return u'<PostViewCount(post_id={}, count={})>'.format(
            self.post_id, self.count)
