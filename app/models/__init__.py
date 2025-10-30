# Database models
from app.models.user import User
from app.models.verification import EmailVerification, PasswordReset
from app.models.education import (
    Course,
    Lesson,
    UserCourseProgress,
    UserLessonProgress,
)