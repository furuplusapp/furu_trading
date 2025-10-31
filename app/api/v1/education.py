from fastapi import APIRouter, Depends, HTTPException, status, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.core.security import verify_token
from app.crud.user import get_user_by_id
from app.crud.education import (
    get_courses,
    get_course,
    create_course,
    update_course,
    delete_course,
    get_lesson,
    get_lessons_by_course,
    mark_lesson_complete,
    get_user_course_progress,
    get_user_lesson_progress,
)
from app.schemas.education import (
    CourseResponse,
    CourseCreate,
    CourseUpdate,
    LessonResponse,
    CourseProgressResponse,
)
from app.core.redis import RedisCache

security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        token_data = verify_token(token, "access")
        if token_data is None:
            return None
        
        user_id = token_data.get("sub")
        if user_id is None:
            return None
        
        user = get_user_by_id(db, user_id=int(user_id))
        return user
    except Exception:
        return None


router = APIRouter()


# Courses endpoints
@router.get("/courses", response_model=List[CourseResponse])
def list_courses(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title, description, instructor"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get all courses with optional filtering"""
    # Cache only for anonymous users (authenticated responses include per-user completion)
    cache_key = None
    if not current_user:
        key_cat = (category or "all").strip().lower()
        key_search = (search or "").strip().lower()
        cache_key = f"education:courses:list:{key_cat}:{key_search}:{skip}:{limit}"
        cached = RedisCache.get(cache_key)
        if cached is not None:
            return cached

    courses = get_courses(db, category=category, search=search, skip=skip, limit=limit)
    
    result = []
    for course in courses:
        course_dict = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "level": course.level.value,
            "duration": course.duration,
            "modules": course.modules,
            "category": course.category,
            "instructor": course.instructor,
            "icon": course.icon,
            "created_at": course.created_at,
            "updated_at": course.updated_at,
            "progress": 0,
            "lessons": [],
        }

        # Get lessons
        lessons = get_lessons_by_course(db, course.id)
        lesson_list = []
        completed_count = 0

        for lesson in lessons:
            lesson_dict = {
                "id": lesson.id,
                "course_id": lesson.course_id,
                "title": lesson.title,
                "duration": lesson.duration,
                "type": lesson.type.value,
                "content": lesson.content,
                "order": lesson.order,
                "completed": False,
                "created_at": lesson.created_at,
                "updated_at": lesson.updated_at,
            }

            # Check user's progress if logged in
            if current_user:
                progress = get_user_lesson_progress(db, current_user.id, lesson.id)
                if progress and progress.completed:
                    lesson_dict["completed"] = True
                    completed_count += 1

            lesson_list.append(lesson_dict)

        # Calculate course progress
        if current_user:
            course_progress = get_user_course_progress(db, current_user.id, course.id)
            if course_progress:
                course_dict["progress"] = course_progress.progress
            elif len(lesson_list) > 0:
                course_dict["progress"] = int((completed_count / len(lesson_list)) * 100)

        course_dict["lessons"] = sorted(lesson_list, key=lambda x: x["order"])
        result.append(course_dict)

    # Store in cache for anonymous users
    if cache_key:
        RedisCache.set(cache_key, result, expire=3600)
    return result


@router.get("/courses/{course_id}", response_model=CourseResponse)
def get_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get course details with lessons"""
    # Cache only for anonymous users
    cache_key = None
    course = None
    if not current_user:
        cache_key = f"education:courses:detail:{course_id}"
        cached = RedisCache.get(cache_key)
        if cached is not None:
            return cached

    course = course or get_course(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    course_dict = {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "level": course.level.value,
        "duration": course.duration,
        "modules": course.modules,
        "category": course.category,
        "instructor": course.instructor,
        "icon": course.icon,
        "created_at": course.created_at,
        "updated_at": course.updated_at,
        "progress": 0,
        "lessons": [],
    }

    # Get lessons
    lessons = get_lessons_by_course(db, course_id)
    lesson_list = []
    completed_count = 0

    for lesson in lessons:
        lesson_dict = {
            "id": lesson.id,
            "course_id": lesson.course_id,
            "title": lesson.title,
            "duration": lesson.duration,
            "type": lesson.type.value,
            "content": lesson.content,
            "order": lesson.order,
            "completed": False,
            "created_at": lesson.created_at,
            "updated_at": lesson.updated_at,
        }

        # Check user's progress if logged in
        if current_user:
            progress = get_user_lesson_progress(db, current_user.id, lesson.id)
            if progress and progress.completed:
                lesson_dict["completed"] = True
                completed_count += 1

        lesson_list.append(lesson_dict)

    # Calculate course progress
    if current_user:
        course_progress = get_user_course_progress(db, current_user.id, course_id)
        if course_progress:
            course_dict["progress"] = course_progress.progress
        elif len(lesson_list) > 0:
            course_dict["progress"] = int((completed_count / len(lesson_list)) * 100)

    course_dict["lessons"] = sorted(lesson_list, key=lambda x: x["order"])
    # Cache for anonymous users
    if cache_key:
        RedisCache.set(cache_key, course_dict, expire=3600)
    return course_dict


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_new_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new course (admin only - implement admin check as needed)"""
    created = create_course(db, course)
    # Invalidate list caches (broad strategy: rely on TTL or delete common keys if tracked)
    # Here we only invalidate detail key of new course (lists will refresh after TTL)
    RedisCache.delete(f"education:courses:detail:{created.id}")
    return created


@router.put("/courses/{course_id}", response_model=CourseResponse)
def update_course_info(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update course (admin only)"""
    course = update_course(db, course_id, course_update)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    # Invalidate detail cache for this course; list caches rely on TTL
    RedisCache.delete(f"education:courses:detail:{course_id}")
    return course


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_endpoint(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete course (admin only)"""
    if not delete_course(db, course_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    # Invalidate detail cache
    RedisCache.delete(f"education:courses:detail:{course_id}")
    return None


# Lessons endpoints
@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson_detail(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get lesson details"""
    lesson = get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    lesson_dict = {
        "id": lesson.id,
        "course_id": lesson.course_id,
        "title": lesson.title,
        "duration": lesson.duration,
        "type": lesson.type.value,
        "content": lesson.content,
        "order": lesson.order,
        "completed": False,
        "created_at": lesson.created_at,
        "updated_at": lesson.updated_at,
    }

    if current_user:
        progress = get_user_lesson_progress(db, current_user.id, lesson_id)
        if progress and progress.completed:
            lesson_dict["completed"] = True

    return lesson_dict


# Progress endpoints
@router.post("/lessons/{lesson_id}/complete", status_code=status.HTTP_200_OK)
def mark_lesson_completed(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a lesson as completed"""
    lesson = get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    progress = mark_lesson_complete(db, current_user.id, lesson_id, completed=True)
    return {"message": "Lesson marked as complete", "lesson_id": lesson_id}


@router.delete("/lessons/{lesson_id}/complete", status_code=status.HTTP_200_OK)
def mark_lesson_incomplete(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a lesson as incomplete"""
    lesson = get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    progress = mark_lesson_complete(db, current_user.id, lesson_id, completed=False)
    return {"message": "Lesson marked as incomplete", "lesson_id": lesson_id}


@router.get("/courses/{course_id}/progress", response_model=CourseProgressResponse)
def get_course_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's progress for a specific course"""
    course = get_course(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    progress = get_user_course_progress(db, current_user.id, course_id)
    lessons = get_lessons_by_course(db, course_id)
    completed = sum(
        1
        for lesson in lessons
        if get_user_lesson_progress(db, current_user.id, lesson.id)
        and get_user_lesson_progress(db, current_user.id, lesson.id).completed
    )

    progress_percentage = progress.progress if progress else 0

    return {
        "course_id": course_id,
        "progress": progress_percentage,
        "completed_lessons": completed,
        "total_lessons": len(lessons),
    }
