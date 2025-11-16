from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    budget: Mapped[int] = mapped_column(Integer)
    revenue: Mapped[int] = mapped_column(Integer)
    runtime: Mapped[int] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"Movie(id={self.id!r}, title{self.title!r}"


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class MovieGenre(Base):
    __tablename__ = "movies_genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey(Movie.id))
    genre_id: Mapped[int] = mapped_column(ForeignKey(Genre.id))


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    gender: Mapped[int] = mapped_column(Integer)
    known_for_department: Mapped[str | None] = mapped_column(String(255))


class MoviePerson(Base):
    __tablename__ = "movies_people"

    id: Mapped[str] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey(Movie.id))
    person_id: Mapped[int] = mapped_column(ForeignKey(Person.id))
    cast_id: Mapped[int | None] = mapped_column(Integer)
    character: Mapped[str | None] = mapped_column(String(255))
    order: Mapped[int | None] = mapped_column(Integer)
    department: Mapped[str | None] = mapped_column(String(255))
    job: Mapped[str | None] = mapped_column(String(255))
