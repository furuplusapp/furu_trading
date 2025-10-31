from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class LessonType(str, Enum):
    DESCRIPTION = "description"


class CourseLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


# Lesson Schemas
class LessonBase(BaseModel):
    title: str
    duration: str
    type: LessonType
    content: Optional[str] = None
    order: int


class LessonCreate(LessonBase):
    course_id: int


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    duration: Optional[str] = None
    type: Optional[LessonType] = None
    content: Optional[str] = None
    order: Optional[int] = None


class LessonResponse(LessonBase):
    id: int
    course_id: int
    completed: Optional[bool] = False  # User-specific completion status
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Course Schemas
class CourseBase(BaseModel):
    title: str
    description: str
    level: CourseLevel
    duration: str
    modules: int
    category: str
    instructor: str
    icon: str


class CourseCreate(CourseBase):
    lessons: List[LessonBase] = []


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[CourseLevel] = None
    duration: Optional[str] = None
    modules: Optional[int] = None
    category: Optional[str] = None
    instructor: Optional[str] = None
    icon: Optional[str] = None


class CourseResponse(CourseBase):
    id: int
    progress: Optional[int] = 0  # User-specific progress percentage
    lessons: List[LessonResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Progress Schemas
class CourseProgressResponse(BaseModel):
    course_id: int
    progress: int
    completed_lessons: int
    total_lessons: int
