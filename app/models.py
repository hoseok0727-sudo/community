from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SourceType(str, Enum):
    DCINSIDE = "dcinside"
    REDDIT = "reddit"
    HACKERNEWS = "hackernews"


class Gallery(Base):
    __tablename__ = "galleries"
    __table_args__ = (
        UniqueConstraint("source_type", "source_key", name="uq_gallery_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(32), index=True)
    source_key: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    posts: Mapped[list[Post]] = relationship(
        back_populates="gallery",
        cascade="all, delete-orphan",
    )
    topics: Mapped[list[Topic]] = relationship(
        back_populates="gallery",
        cascade="all, delete-orphan",
    )


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("gallery_id", "external_id", name="uq_post_gallery_external"),
        Index("ix_posts_gallery_published_at", "gallery_id", "published_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gallery_id: Mapped[int] = mapped_column(
        ForeignKey("galleries.id", ondelete="CASCADE"),
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(255), default="")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    upvote_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    raw_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    gallery: Mapped[Gallery] = relationship(back_populates="posts")
    topic_links: Mapped[list[TopicPost]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )


class TopicRun(Base):
    __tablename__ = "topic_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    window_hours: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        index=True,
    )

    topics: Mapped[list[Topic]] = relationship(back_populates="run", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (Index("ix_topics_gallery_created", "gallery_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gallery_id: Mapped[int] = mapped_column(
        ForeignKey("galleries.id", ondelete="CASCADE"),
        index=True,
    )
    run_id: Mapped[int] = mapped_column(ForeignKey("topic_runs.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    trend: Mapped[str] = mapped_column(String(32), default="stable")
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    gallery: Mapped[Gallery] = relationship(back_populates="topics")
    run: Mapped[TopicRun] = relationship(back_populates="topics")
    post_links: Mapped[list[TopicPost]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
    )


class TopicPost(Base):
    __tablename__ = "topic_posts"
    __table_args__ = (UniqueConstraint("topic_id", "post_id", name="uq_topic_post"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    rank: Mapped[int] = mapped_column(Integer, default=1)

    topic: Mapped[Topic] = relationship(back_populates="post_links")
    post: Mapped[Post] = relationship(back_populates="topic_links")
