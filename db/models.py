from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, Date
from sqlalchemy.orm import relationship
from db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    user_type = Column(String(50), nullable=False)

    resumes = relationship("Resume", back_populates="user")
    reviews = relationship("Review", back_populates="guide")

    guide_languages = relationship("GuideLanguages", back_populates="guide")
    guide_addresses = relationship("GuideAddress", back_populates="guide")
    guide_bookings = relationship("BookGuide", back_populates="guide")


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    guide_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rating = Column(Float, nullable=False)

    guide = relationship("User", back_populates="reviews")

class Region(Base):
    __tablename__ = "regions"

    region_id = Column(Integer, primary_key=True, index=True)
    region = Column(String(255), nullable=False, unique=True)


class City(Base):
    __tablename__ = "cities"

    city_id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    city = Column(String(255), nullable=False, unique=True)

    region = relationship("Region", back_populates="cities")


class Address(Base):
    __tablename__ = "addresses"

    address_id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.city_id"), nullable=False)

    region = relationship("Region")
    city = relationship("City")

    guide_addresses = relationship("GuideAddress", back_populates="address")
    tours = relationship("Tour", back_populates="address")


class Resume(Base):
    __tablename__ = "resumes"

    resume_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    languages = Column(Text, nullable=True)  # Comma-separated list of language IDs
    addresses = Column(Text, nullable=True)  # Comma-separated list of address IDs
    bio = Column(Text, nullable=True)
    experience_start_date = Column(Date, nullable=True)
    rating = Column(Float, nullable=True)

    user = relationship("User", back_populates="resumes")

class Language(Base):
    __tablename__ = "languages"

    language_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    guide_languages = relationship("GuideLanguages", back_populates="language")



class GuideLanguages(Base):
    __tablename__ = "guide_languages"

    guide_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    language_id = Column(Integer, ForeignKey("languages.language_id"), primary_key=True)

    guide = relationship("User", back_populates="guide_languages")
    language = relationship("Language", back_populates="guide_languages")


class GuideAddress(Base):
    __tablename__ = "guide_address"

    guide_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    address_id = Column(Integer, ForeignKey("addresses.address_id"), primary_key=True)

    guide = relationship("User", back_populates="guide_addresses")
    address = relationship("Address", back_populates="guide_addresses")


class Tour(Base):
    __tablename__ = "tours"

    tour_id = Column(Integer, primary_key=True, index=True)
    address_id = Column(Integer, ForeignKey("addresses.address_id"), nullable=False)
    language = Column(String(255), nullable=False)
    guest_count = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    price_type = Column(String(50), nullable=False)
    payment_type = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    duration = Column(String(50), nullable=False)
    about = Column(Text, nullable=True)

    address = relationship("Address", back_populates="tours")
    tour_bookings = relationship("BookTour", back_populates="tour")


class BookGuide(Base):
    __tablename__ = "book_guide"

    book_id = Column(Integer, primary_key=True, index=True)
    guide_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    guest_count = Column(Integer, nullable=False)
    reserve_count = Column(Integer, nullable=False)

    guide = relationship("User", back_populates="guide_bookings")


class BookTour(Base):
    __tablename__ = "book_tour"

    book_id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.tour_id"), nullable=False)
    reserve_count = Column(Integer, nullable=False)

    tour = relationship("Tour", back_populates="tour_bookings")
