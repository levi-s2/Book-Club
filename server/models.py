from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy_serializer import SerializerMixin
from flask_bcrypt import Bcrypt
import datetime

# Initialize the extensions
metadata = MetaData()
db = SQLAlchemy(metadata=metadata)
bcrypt = Bcrypt()

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    
    id = db.Column(Integer, primary_key=True)
    username = db.Column(String, unique=True, nullable=False)
    email = db.Column(String, unique=True, nullable=False)
    _password_hash = db.Column(String, nullable=False)

    book_clubs_created = relationship('BookClub', back_populates='creator')
    memberships = relationship('Membership', back_populates='user')
    reviews = relationship('Review', back_populates='user')

    serialize_rules = ('-book_clubs_created.creator', '-memberships.user', '-reviews.user')

    @property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password):
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates('email')
    def validate_email(self, key, address):
        assert '@' in address
        return address

    @validates('username')
    def validate_username(self, key, username):
        assert username is not None and len(username) > 0
        return username

    def __repr__(self):
        return f'<User {self.id}. {self.username}>'


class BookClub(db.Model, SerializerMixin):
    __tablename__ = 'book_clubs'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String, nullable=False)
    description = db.Column(Text, nullable=True)
    created_by = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = db.Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    creator = relationship('User', back_populates='book_clubs_created')
    members = relationship('Membership', back_populates='book_club')
    current_reading = relationship('CurrentReading', uselist=False, back_populates='book_club')
    reviews = relationship('Review', back_populates='book_club')

    serialize_rules = ('-creator.book_clubs_created', '-members.book_club', '-reviews.book_club')

    @validates('name')
    def validate_name(self, key, name):
        assert name is not None and len(name) > 0
        return name

    def __repr__(self):
        return f'<BookClub {self.id}. {self.name}>'


class Book(db.Model, SerializerMixin):
    __tablename__ = 'books'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String, nullable=False)
    author = db.Column(String, nullable=False)
    image_url = db.Column(String, nullable=True)
    genre_id = db.Column(Integer, ForeignKey('genres.id'), nullable=False)

    genre = relationship('Genre', back_populates='books')
    current_reading = relationship('CurrentReading', back_populates='book')
    reviews = relationship('Review', back_populates='book')

    serialize_rules = ('-genre.books', '-current_reading.book', '-reviews.book')

    @validates('title')
    def validate_title(self, key, title):
        assert title is not None and len(title) > 0
        return title

    @validates('author')
    def validate_author(self, key, author):
        assert author is not None and len(author) > 0
        return author

    def __repr__(self):
        return f'<Book {self.id}. {self.title}>'


class Genre(db.Model, SerializerMixin):
    __tablename__ = 'genres'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String, nullable=False, unique=True)

    books = relationship('Book', back_populates='genre')

    serialize_rules = ('-books.genre',)

    @validates('name')
    def validate_name(self, key, name):
        assert name is not None and len(name) > 0
        return name

    def __repr__(self):
        return f'<Genre {self.id}. {self.name}>'


class Membership(db.Model, SerializerMixin):
    __tablename__ = 'memberships'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    book_club_id = db.Column(Integer, ForeignKey('book_clubs.id'), nullable=False)

    user = relationship('User', back_populates='memberships')
    book_club = relationship('BookClub', back_populates='members')

    serialize_rules = ('-user.memberships', '-book_club.members')

    def __repr__(self):
        return f'<Membership {self.id}. User: {self.user_id}, BookClub: {self.book_club_id}>'


class CurrentReading(db.Model, SerializerMixin):
    __tablename__ = 'current_readings'
    
    id = db.Column(Integer, primary_key=True)
    book_club_id = db.Column(Integer, ForeignKey('book_clubs.id'), nullable=False)
    book_id = db.Column(Integer, ForeignKey('books.id'), nullable=False)
    started_at = db.Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    book_club = relationship('BookClub', back_populates='current_reading')
    book = relationship('Book', back_populates='current_reading')

    serialize_rules = ('-book_club.current_reading', '-book.current_reading')

    def __repr__(self):
        return f'<CurrentReading {self.id}. BookClub: {self.book_club_id}, Book: {self.book_id}>'


class Review(db.Model, SerializerMixin):
    __tablename__ = 'reviews'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    book_id = db.Column(Integer, ForeignKey('books.id'), nullable=False)
    book_club_id = db.Column(Integer, ForeignKey('book_clubs.id'), nullable=False)  # Add this line
    content = db.Column(Text, nullable=False)
    rating = db.Column(Integer, nullable=False)
    created_at = db.Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = db.Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    user = relationship('User', back_populates='reviews')
    book = relationship('Book', back_populates='reviews')
    book_club = relationship('BookClub', back_populates='reviews')  # Add this line

    serialize_rules = ('-user.reviews', '-book.reviews', '-book_club.reviews')

    @validates('rating')
    def validate_rating(self, key, rating):
        assert 1 <= rating <= 5
        return rating

    def __repr__(self):
        return f'<Review {self.id}. User: {self.user_id}, Book: {self.book_id}, Rating: {self.rating}>'
