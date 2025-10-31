from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models.education import (
    Course,
    Lesson,
    UserCourseProgress,
    UserLessonProgress,
)
from app.schemas.education import (
    CourseCreate,
    CourseUpdate,
    LessonCreate,
    LessonUpdate,
)


# Course CRUD
def get_course(db: Session, course_id: int) -> Optional[Course]:
    """Get course by ID"""
    return db.query(Course).filter(Course.id == course_id).first()


def get_courses(
    db: Session,
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Course]:
    """Get all courses with optional filtering"""
    query = db.query(Course)

    if category:
        query = query.filter(Course.category.ilike(f"%{category}%"))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Course.title.ilike(search_term))
            | (Course.description.ilike(search_term))
            | (Course.instructor.ilike(search_term))
        )

    return query.offset(skip).limit(limit).all()


def create_course(db: Session, course: CourseCreate) -> Course:
    """Create a new course with lessons"""
    db_course = Course(
        title=course.title,
        description=course.description,
        level=course.level,
        duration=course.duration,
        modules=course.modules,
        category=course.category,
        instructor=course.instructor,
        icon=course.icon,
    )
    db.add(db_course)
    db.flush()  # Get the course ID

    # Create lessons
    for order, lesson_data in enumerate(course.lessons, start=1):
        db_lesson = Lesson(
            course_id=db_course.id,
            title=lesson_data.title,
            duration=lesson_data.duration,
            type=lesson_data.type,
            content=lesson_data.content,
            order=order,
        )
        db.add(db_lesson)

    db.commit()
    db.refresh(db_course)
    return db_course


def update_course(db: Session, course_id: int, course_update: CourseUpdate) -> Optional[Course]:
    """Update course"""
    db_course = get_course(db, course_id)
    if not db_course:
        return None

    update_data = course_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_course, field, value)

    db.commit()
    db.refresh(db_course)
    return db_course


def delete_course(db: Session, course_id: int) -> bool:
    """Delete course"""
    db_course = get_course(db, course_id)
    if not db_course:
        return False
    db.delete(db_course)
    db.commit()
    return True


# Lesson CRUD
def get_lesson(db: Session, lesson_id: int) -> Optional[Lesson]:
    """Get lesson by ID"""
    return db.query(Lesson).filter(Lesson.id == lesson_id).first()


def get_lessons_by_course(db: Session, course_id: int) -> List[Lesson]:
    """Get all lessons for a course"""
    return (
        db.query(Lesson)
        .filter(Lesson.course_id == course_id)
        .order_by(Lesson.order)
        .all()
    )


def create_lesson(db: Session, lesson: LessonCreate) -> Lesson:
    """Create a new lesson"""
    db_lesson = Lesson(**lesson.model_dump())
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def update_lesson(db: Session, lesson_id: int, lesson_update: LessonUpdate) -> Optional[Lesson]:
    """Update lesson"""
    db_lesson = get_lesson(db, lesson_id)
    if not db_lesson:
        return None

    update_data = lesson_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_lesson, field, value)

    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def delete_lesson(db: Session, lesson_id: int) -> bool:
    """Delete lesson"""
    db_lesson = get_lesson(db, lesson_id)
    if not db_lesson:
        return False
    db.delete(db_lesson)
    db.commit()
    return True


# Progress CRUD
def get_user_course_progress(
    db: Session, user_id: int, course_id: int
) -> Optional[UserCourseProgress]:
    """Get user's progress for a specific course"""
    return (
        db.query(UserCourseProgress)
        .filter(
            UserCourseProgress.user_id == user_id,
            UserCourseProgress.course_id == course_id,
        )
        .first()
    )


def get_or_create_user_course_progress(
    db: Session, user_id: int, course_id: int
) -> UserCourseProgress:
    """Get or create user course progress"""
    progress = get_user_course_progress(db, user_id, course_id)
    if not progress:
        progress = UserCourseProgress(user_id=user_id, course_id=course_id, progress=0)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def update_user_course_progress(
    db: Session, user_id: int, course_id: int
) -> UserCourseProgress:
    """Calculate and update user's course progress"""
    progress = get_or_create_user_course_progress(db, user_id, course_id)

    # Count completed lessons
    completed_count = (
        db.query(func.count(UserLessonProgress.id))
        .join(Lesson, UserLessonProgress.lesson_id == Lesson.id)
        .filter(
            UserLessonProgress.user_id == user_id,
            Lesson.course_id == course_id,
            UserLessonProgress.completed == True,
        )
        .scalar()
    )

    # Count total lessons
    total_count = (
        db.query(func.count(Lesson.id)).filter(Lesson.course_id == course_id).scalar()
    )

    # Calculate progress percentage
    if total_count > 0:
        progress.progress = int((completed_count / total_count) * 100)
    else:
        progress.progress = 0

    db.commit()
    db.refresh(progress)
    return progress


def get_user_lesson_progress(
    db: Session, user_id: int, lesson_id: int
) -> Optional[UserLessonProgress]:
    """Get user's progress for a specific lesson"""
    return (
        db.query(UserLessonProgress)
        .filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id,
        )
        .first()
    )


def mark_lesson_complete(
    db: Session, user_id: int, lesson_id: int, completed: bool = True
) -> UserLessonProgress:
    """Mark a lesson as complete or incomplete"""
    progress = get_user_lesson_progress(db, user_id, lesson_id)

    if not progress:
        progress = UserLessonProgress(
            user_id=user_id, lesson_id=lesson_id, completed=completed
        )
        db.add(progress)
    else:
        progress.completed = completed

    if completed:
        from datetime import datetime
        progress.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(progress)

    # Update course progress
    lesson = get_lesson(db, lesson_id)
    if lesson:
        update_user_course_progress(db, user_id, lesson.course_id)

    return progress
