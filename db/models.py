from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, Date, ARRAY, Time, Table
from sqlalchemy.orm import relationship
from db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.address_id"), nullable=True)
    user_type = Column(String(50), nullable=False)

    address = relationship("Address", back_populates="users")

    resumes = relationship("Resume", back_populates="user")

    guide_reviews = relationship(
        "Review",
        secondary="resumes",
        primaryjoin="User.user_id == Resume.guide_id",
        secondaryjoin="Resume.resume_id == Review.resume_id",
        viewonly=True
    )

    tourist_reviews = relationship(
        "Review",
        foreign_keys="[Review.tourist_id]"
    )

    guide_languages = relationship("GuideLanguages", back_populates="guide")
    guide_addresses = relationship("GuideAddress", back_populates="guide")

    guide_bookings = relationship(
        "BookGuide",
        back_populates="guide",
        foreign_keys="[BookGuide.guide_id]"
    )
    tourist_bookings = relationship(
        "BookGuide",
        back_populates="tourist",
        foreign_keys="[BookGuide.tourist_id]"
    )
    tour_reviews = relationship(
        "TourReview",
        back_populates="tourist",
        foreign_keys="[TourReview.tourist_id]"
    )


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.resume_id"), nullable=False)
    tourist_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rating = Column(Float, nullable=False)

    resume = relationship("Resume", back_populates="resume_reviews")
    tourist = relationship("User", back_populates="tourist_reviews")


class TourReview(Base):
    __tablename__ = "tour_reviews"

    tour_review_id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.tour_id"), nullable=False)
    tourist_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rating = Column(Float, nullable=False)

    tour = relationship("Tour", back_populates="tour_reviews")
    tourist = relationship("User", back_populates="tour_reviews")

class Region(Base):
    __tablename__ = "regions"

    region_id = Column(Integer, primary_key=True, index=True)
    region = Column(String(255), nullable=False, unique=True)

    cities = relationship("City", back_populates="region")


class City(Base):
    __tablename__ = "cities"

    city_id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    city = Column(String(255), nullable=False, unique=True)

    region = relationship("Region", back_populates="cities")

# Many-to-Many relationship for Tour <-> Address
tour_addresses = Table(
    "tour_addresses",
    Base.metadata,
    Column("tour_id", Integer, ForeignKey("tours.tour_id"), primary_key=True),
    Column("address_id", Integer, ForeignKey("addresses.address_id"), primary_key=True),
)

resume_addresses = Table(
    'resume_addresses',
    Base.metadata,
    Column('resume_id', Integer, ForeignKey('resumes.resume_id')),
    Column('address_id', Integer, ForeignKey('addresses.address_id')),
)


class Address(Base):
    __tablename__ = "addresses"

    address_id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.city_id"), nullable=False)

    region = relationship("Region")
    city = relationship("City")

    users = relationship("User", back_populates="address")
    # Many-to-Many with Tour
    tours = relationship("Tour", secondary="tour_addresses", back_populates="addresses")
    # Many-to-Many with Guide
    guide_addresses = relationship("GuideAddress", back_populates="address")
    # Many-to-Many with Resume
    resumes = relationship("Resume", secondary=resume_addresses, back_populates="addresses")

# Many-to-Many relationship for Tour <-> Language
tour_languages = Table(
    "tour_languages",
    Base.metadata,
    Column("tour_id", Integer, ForeignKey("tours.tour_id"), primary_key=True),
    Column("language_id", Integer, ForeignKey("languages.language_id"), primary_key=True),
)

resume_languages = Table(
    'resume_languages',
    Base.metadata,
    Column('resume_id', Integer, ForeignKey('resumes.resume_id')),
    Column('language_id', Integer, ForeignKey('languages.language_id')),
)
class Language(Base):
    __tablename__ = "languages"

    language_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # Many-to-Many with Tour
    tours = relationship("Tour", secondary="tour_languages", back_populates="languages")
    # Many-to-Many with Guide
    guide_languages = relationship("GuideLanguages", back_populates="language")
    # Many-to-Many with Resume
    resumes = relationship("Resume", secondary=resume_languages, back_populates="languages")

class Resume(Base):
    __tablename__ = "resumes"

    resume_id = Column(Integer, primary_key=True, index=True)
    guide_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    bio = Column(Text, nullable=True)
    experience_start_date = Column(Date, nullable=True)
    price = Column(Integer, nullable=True)
    price_type = Column(Text, nullable=True)

    user = relationship("User", back_populates="resumes")
    languages = relationship("Language", secondary=resume_languages, back_populates="resumes")
    addresses = relationship("Address", secondary=resume_addresses, back_populates="resumes")
    resume_reviews = relationship("Review", back_populates="resume")


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
    title = Column(String, nullable=False)
    guide_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    guest_count = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    price_type = Column(String(50), nullable=False)
    payment_type = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    departure_time = Column(Time, nullable=False)
    return_time = Column(Time, nullable=False)
    duration = Column(Integer, nullable=False)
    dress_code = Column(String(255), nullable=True)
    not_included = Column(Text, nullable=True)
    included = Column(Text, nullable=True)
    photo_gallery = Column(ARRAY(String), nullable=True)
    about = Column(Text, nullable=True)

    # Many-to-Many relationships
    addresses = relationship("Address", secondary=tour_addresses, back_populates="tours")
    languages = relationship("Language", secondary=tour_languages, back_populates="tours")

    tour_bookings = relationship("BookTour", back_populates="tour")
    tour_reviews = relationship("TourReview", back_populates="tour")


class BookGuide(Base):
    __tablename__ = "book_guide"

    book_id = Column(Integer, primary_key=True, index=True)
    guide_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reserve_count = Column(Integer, nullable=False)
    tourist_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    guide = relationship("User", back_populates="guide_bookings", foreign_keys=[guide_id])
    tourist = relationship("User", back_populates="tourist_bookings", foreign_keys=[tourist_id])



class BookTour(Base):
    __tablename__ = "book_tour"

    book_id = Column(Integer, primary_key=True, index=True)
    tourist_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    tour_id = Column(Integer, ForeignKey("tours.tour_id"), nullable=False)
    reserve_count = Column(Integer, nullable=False)

    tour = relationship("Tour", back_populates="tour_bookings")
