from datetime import datetime, time

from pydantic import BaseModel, EmailStr
from typing import Optional, List

from db.models import Resume


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    address: Optional[str]
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
    address: Optional[str]
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
    user_id: int
    rating: float
    languages: List[LanguageOut]
    addresses: List[AddressOut]
    user_name: str
    price: int
    price_type: str


    class Config:
        orm_mode = True
        from_attributes = True

    @classmethod
    def from_orm(cls, resume: Resume, user_name: str):
        return cls(
            **resume.__dict__,
            user_name=user_name
        )


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

    @classmethod
    def from_orm(cls, obj):
        data = obj.__dict__.copy()
        data.pop('_sa_instance_state', None)
        data["destination_ids"] = [address.address_id for address in obj.addresses] if obj.addresses else []
        data["language_ids"] = [lang.language_id for lang in obj.languages] if obj.languages else []
        return cls(**data)

    class Config:
        orm_mode = True



class BookGuideBase(BaseModel):
    guide_id: int
    reserve_count: int


class BookGuideCreate(BookGuideBase):
    pass


class BookGuideOut(BookGuideBase):
    book_id: int

    class Config:
        orm_mode = True


class BookTourBase(BaseModel):
    tour_id: int
    reserve_count: int


class BookTourCreate(BookTourBase):
    pass


class BookTourOut(BookTourBase):
    book_id: int

    class Config:
        orm_mode = True
