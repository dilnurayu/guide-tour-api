from datetime import datetime

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    address: Optional[str]
    user_type: str


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


class ResumeBase(BaseModel):
    user_id: int
    languages: list[int] | None = None
    addresses: list[int] | None = None
    bio: str | None = None
    experience_start_date: datetime | None = None
    rating: float | None = None


class ResumeCreate(ResumeBase):
    pass


class ResumeOut(ResumeBase):
    resume_id: int

    class Config:
        orm_mode = True


class ReviewBase(BaseModel):
    guide_id: int
    title: str
    description: str | None = None
    rating: float


class ReviewCreate(ReviewBase):
    pass


class ReviewOut(ReviewBase):
    review_id: int

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


class TourBase(BaseModel):
    address_id: int
    language: str
    guest_count: int
    price: float
    price_type: str
    payment_type: str
    date: datetime
    duration: str
    about: str | None = None

class Language(BaseModel):
    language_id: int
    name: str


class TourCreate(TourBase):
    pass


class TourOut(TourBase):
    tour_id: int

    class Config:
        orm_mode = True


class BookGuideBase(BaseModel):
    guide_id: int
    guest_count: int
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
