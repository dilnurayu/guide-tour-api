from datetime import datetime, time, date

from pydantic import BaseModel, EmailStr
from typing import Optional, List


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    address_id: Optional[int]
    user_type: str

class SignIn(BaseModel):
    email: str
    password: str

class LanguageCreate(BaseModel):
    name: str

class LanguageOut(BaseModel):
    language_id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True

class UserOut(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    address_id: Optional[int]
    user_type: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class RegionBase(BaseModel):
    region: str


class RegionCreate(RegionBase):
    pass


class RegionOut(RegionBase):
    region_id: int

    class Config:
        orm_mode = True


class CityBase(BaseModel):
    region_id: int
    city: str


class CityCreate(CityBase):
    pass


class CityOut(CityBase):
    city_id: int

    class Config:
        orm_mode = True


class AddressBase(BaseModel):
    region_id: int
    city_id: int


class AddressCreate(AddressBase):
    pass


class AddressOut(AddressBase):
    address_id: int

    class Config:
        orm_mode = True
        from_attributes = True


class ResumeBase(BaseModel):
    bio: Optional[str] = None
    experience_start_date: Optional[datetime] = None
    languages: Optional[List[int]] = None
    addresses: Optional[List[int]] = None
    price: Optional[int] = None
    price_type: Optional[str] = None

class ResumeCreate(ResumeBase):
    bio: str
    experience_start_date: datetime
    languages: List[int]
    addresses: List[int]
    price: int
    price_type: str

class ResumeOut(ResumeBase):
    resume_id: int
    guide_id: int
    rating: float
    languages: List[LanguageOut]
    addresses: List[AddressOut]
    price: int
    price_type: str
    guide_name: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, resume, guide_name: Optional[str] = None):
        resume_dict = {
            "resume_id": resume.resume_id,
            "guide_id": resume.guide_id,
            "bio": resume.bio,
            "experience_start_date": resume.experience_start_date,
            "languages": resume.languages,
            "addresses": resume.addresses,
            "price": resume.price,
            "price_type": resume.price_type,
            "rating": getattr(resume, 'rating', 0.0),
            "guide_name": guide_name,
        }
        return cls(**resume_dict)



class ReviewBase(BaseModel):
    resume_id: int
    title: str
    description: str | None = None
    rating: float


class ReviewCreate(ReviewBase):
    pass


class ReviewOut(ReviewBase):
    review_id: int

    class Config:
        orm_mode = True


class TourReviewBase(BaseModel):
    tour_id: int
    title: str
    description: str
    rating: float

class TourReviewCreate(TourReviewBase):
    pass

class TourReviewOut(TourReviewBase):
    tour_review_id: int

    class Config:
        orm_mode = True

class GuideLanguageBase(BaseModel):
    guide_id: int
    language_id: int


class GuideLanguageCreate(GuideLanguageBase):
    pass


class GuideLanguageOut(GuideLanguageBase):
    class Config:
        orm_mode = True


class GuideAddressBase(BaseModel):
    guide_id: int
    address_id: int


class GuideAddressCreate(GuideAddressBase):
    pass


class GuideAddressOut(GuideAddressBase):
    class Config:
        orm_mode = True

class Language(BaseModel):
    language_id: int
    name: str

class TourBase(BaseModel):
    guest_count: int
    title: str
    price: float
    price_type: str
    payment_type: str
    date: datetime
    departure_time: time
    return_time: time
    duration: int
    dress_code: Optional[str] = None
    not_included: Optional[str] = None
    included: Optional[str] = None
    photo_gallery: List[str] = None
    about: Optional[str] = None

class TourCreate(TourBase):
    destination_ids: List[int]
    language_ids: List[int]


class TourOut(TourBase):
    tour_id: int
    destination_ids: List[int]
    language_ids: List[int]
    average_rating: float = 0.0

    @classmethod
    def from_orm(cls, obj):
        data = obj.__dict__.copy()
        data.pop('_sa_instance_state', None)
        data["destination_ids"] = [address.address_id for address in obj.addresses] if obj.addresses else []
        data["language_ids"] = [lang.language_id for lang in obj.languages] if obj.languages else []

        if obj.tour_reviews:
            data["average_rating"] = sum(review.rating for review in obj.tour_reviews) / len(obj.tour_reviews)
        else:
            data["average_rating"] = 0.0

        return cls(**data)

class BookGuideCreate(BaseModel):
    guide_id: int
    tour_date: date
    reserve_count: int
    language_id: int
    message: str

class BookGuideOut(BookGuideCreate):
    book_id: int
    confirmed: bool

    class Config:
        orm_mode = True

class BookTourCreate(BaseModel):
    tour_id: int
    reserve_count: int
    language_id: int
    message: str

class BookTourOut(BookTourCreate):
    book_id: int
    confirmed: bool

    class Config:
        orm_mode = True


class ProfileOut(BaseModel):
    user_name: str
    email: str
    address_id: int