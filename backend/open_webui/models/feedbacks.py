import logging
import time
import uuid
from typing import Optional

from sqlalchemy.orm import Session
from open_webui.internal.db import Base, JSONField, get_db, get_db_context
from open_webui.models.users import User
from open_webui.models.chats import Chats
from open_webui.models.users import User, UserModel

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, Text, JSON, Boolean, func, case, cast
from sqlalchemy.orm import defer

log = logging.getLogger(__name__)


####################
# Feedback DB Schema
####################


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Text, primary_key=True, unique=True)
    user_id = Column(Text)
    version = Column(BigInteger, default=0)
    type = Column(Text)
    data = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)
    snapshot = Column(JSON, nullable=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)
    chat_id = Column(Text)


class FeedbackModel(BaseModel):
    id: str
    user_id: str
    version: int
    type: str
    data: Optional[dict] = None
    meta: Optional[dict] = None
    snapshot: Optional[dict] = None
    created_at: int
    updated_at: int
    chat_id: str
    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    version: int
    type: str
    data: Optional[dict] = None
    meta: Optional[dict] = None
    snapshot: Optional[dict] = None
    created_at: int
    updated_at: int


class FeedbackIdResponse(BaseModel):
    id: str
    user_id: str
    created_at: int
    updated_at: int


class LeaderboardFeedbackData(BaseModel):
    """Minimal feedback data for leaderboard computation (excludes snapshot/meta)."""

    id: str
    data: Optional[dict] = None


class RatingData(BaseModel):
    rating: Optional[str | int] = None
    model_id: Optional[str] = None
    sibling_model_ids: Optional[list[str]] = None
    reason: Optional[str] = None
    comment: Optional[str] = None
    model_config = ConfigDict(extra="allow", protected_namespaces=())


class MetaData(BaseModel):
    arena: Optional[bool] = None
    chat_id: Optional[str] = None
    message_id: Optional[str] = None
    tags: Optional[list[str]] = None
    model_config = ConfigDict(extra="allow")


class SnapshotData(BaseModel):
    chat: Optional[dict] = None
    model_config = ConfigDict(extra="allow")


class FeedbackForm(BaseModel):
    type: str
    data: Optional[RatingData] = None
    meta: Optional[dict] = None
    snapshot: Optional[SnapshotData] = None
    model_config = ConfigDict(extra="allow")


class FeedbackEvaluate(BaseModel):
    model_id: str
    count: int
    possible: int
    negative: int


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str = "pending"

    last_active_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


class FeedbackUserResponse(BaseModel):
    id: str
    user_id: str
    version: int
    type: str
    data: Optional[dict] = None
    meta: Optional[dict] = None
    snapshot: Optional[dict] = None
    chat_title: Optional[str] = None
    created_at: int
    updated_at: int
    chat_id: str
    user: Optional[UserModel] = None
    model_config = ConfigDict(from_attributes=True)

class FeedbackUserPaginationResponse(BaseModel):
    count: int
    list: list[FeedbackUserResponse]


class FeedbackListResponse(BaseModel):
    items: list[FeedbackUserResponse]
    total: int


class ModelHistoryEntry(BaseModel):
    date: str
    won: int
    lost: int


class ModelHistoryResponse(BaseModel):
    model_id: str
    history: list[ModelHistoryEntry]


class FeedbackTable:
    def insert_new_feedback(
        self, user_id: str, form_data: FeedbackForm, db: Optional[Session] = None
    ) -> Optional[FeedbackModel]:
        with get_db_context(db) as db:
            id = str(uuid.uuid4())
            chat_id = form_data.meta.get('chat_id') if form_data.meta else None
            feedback = FeedbackModel(
                **{
                    "id": id,
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "version": 0,
                    **form_data.model_dump(),
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )
            try:
                result = Feedback(**feedback.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                if result:
                    return FeedbackModel.model_validate(result)
                else:
                    return None
            except Exception as e:
                log.exception(f"Error creating a new feedback: {e}")
                return None

    def get_feedback_by_id(
        self, id: str, db: Optional[Session] = None
    ) -> Optional[FeedbackModel]:
        try:
            with get_db_context(db) as db:
                feedback = db.query(Feedback).filter_by(id=id).first()
                if not feedback:
                    return None
                return FeedbackModel.model_validate(feedback)
        except Exception:
            return None

    def get_feedback_by_id_and_user_id(
        self, id: str, user_id: str, db: Optional[Session] = None
    ) -> Optional[FeedbackModel]:
        try:
            with get_db_context(db) as db:
                feedback = db.query(Feedback).filter_by(id=id, user_id=user_id).first()
                if not feedback:
                    return None
                return FeedbackModel.model_validate(feedback)
        except Exception:
            return None

    def get_feedback_items(
        self,
        filter: dict = {},
        skip: int = 0,
        limit: int = 30,
        db: Optional[Session] = None,
    ) -> FeedbackListResponse:
        with get_db_context(db) as db:
            query = db.query(Feedback, User).join(User, Feedback.user_id == User.id)

            if filter:
                order_by = filter.get("order_by")
                direction = filter.get("direction")

                if order_by == "username":
                    if direction == "asc":
                        query = query.order_by(User.name.asc())
                    else:
                        query = query.order_by(User.name.desc())
                elif order_by == "model_id":
                    # it's stored in feedback.data['model_id']
                    if direction == "asc":
                        query = query.order_by(
                            Feedback.data["model_id"].as_string().asc()
                        )
                    else:
                        query = query.order_by(
                            Feedback.data["model_id"].as_string().desc()
                        )
                elif order_by == "rating":
                    # it's stored in feedback.data['rating']
                    if direction == "asc":
                        query = query.order_by(
                            Feedback.data["rating"].as_string().asc()
                        )
                    else:
                        query = query.order_by(
                            Feedback.data["rating"].as_string().desc()
                        )
                elif order_by == "updated_at":
                    if direction == "asc":
                        query = query.order_by(Feedback.updated_at.asc())
                    else:
                        query = query.order_by(Feedback.updated_at.desc())

            else:
                query = query.order_by(Feedback.created_at.desc())

            # Count BEFORE pagination
            total = query.count()

            if skip:
                query = query.offset(skip)
            if limit:
                query = query.limit(limit)

            items = query.all()

            feedbacks = []
            for feedback, user in items:
                feedback_model = FeedbackModel.model_validate(feedback)
                user_model = UserResponse.model_validate(user)
                feedbacks.append(
                    FeedbackUserResponse(**feedback_model.model_dump(), user=user_model)
                )

            return FeedbackListResponse(items=feedbacks, total=total)

    def get_all_feedbacks(self, db: Optional[Session] = None) -> list[FeedbackModel]:
        with get_db_context(db) as db:
            return [
                FeedbackModel.model_validate(feedback)
                for feedback in db.query(Feedback)
                .order_by(Feedback.updated_at.desc())
                .all()
            ]

    # TODO: renesas
    def get_all_feedbacks_with_user(self, db: Optional[Session] = None) -> list[FeedbackUserResponse]:
        with get_db_context(db) as db:
            results = (
                db.query(Feedback, User)
                .outerjoin(User, Feedback.user_id == User.id)
                .order_by(Feedback.updated_at.desc())
                .all()
            )

            return [
                FeedbackUserResponse(
                    **feedback.__dict__,
                    user=UserModel.model_validate(user) if user else None
                )
                for feedback, user in results
            ]

    def get_all_feedbacks_with_user_pagination(self, limit: int = 10, page: int = 1, db: Optional[Session] = None) -> FeedbackUserPaginationResponse:
        # Calculate the offset based on page and limit
        offset = (page - 1) * limit
        with get_db_context(db) as db:
            count = db.query(func.count(Feedback.id)).scalar()
            snapshot_chat_title = func.json_extract(Feedback.snapshot, '$.chat.title').label('chat_title')

            results = (
                db.query(Feedback, User, snapshot_chat_title)
                .options(defer(Feedback.snapshot))
                .outerjoin(User, Feedback.user_id == User.id)
                .order_by(Feedback.updated_at.desc())
                .limit(limit)  # Limit the number of results by the specified limit
                .offset(offset)  # Skip the specified number of results
                .all()
            )

            return FeedbackUserPaginationResponse.model_validate({
                'count': count,
                'list': [
                    FeedbackUserResponse(
                        **{**feedback.__dict__, 'chat_title': chat_title},
                        user=UserModel.model_validate(user) if user else None
                    )
                    for feedback, user, chat_title in results
                ]
            })

    def get_feedbacks_grouped_by_model_id(self, db: Optional[Session] = None) -> list[FeedbackEvaluate]:
        with get_db_context(db) as db:
            # Aggregate feedback based on the model_id in data
            results = (
                db.query(
                    func.json_extract(Feedback.data, '$.model_id').label('model_id'),
                    func.sum(
                        case(
                            (cast(func.json_extract(Feedback.data, '$.rating'), BigInteger) > 0, 1),
                            else_=0
                        )
                    ).label('possible'),
                    func.sum(
                        case(
                            (cast(func.json_extract(Feedback.data, '$.rating'), BigInteger) < 0, 1),
                            else_=0
                        )
                    ).label('negative')
                )
                .group_by(func.json_extract(Feedback.data, '$.model_id'))
                .all()
            )

            # Transform the results into a list of dictionaries for easier consumption
            feedback_summary = [
                FeedbackEvaluate(**{
                    "model_id": result.model_id,
                    "count": result.possible + result.negative,
                    "possible": result.possible,
                    "negative": result.negative
                })
                for result in results
            ]

            return feedback_summary

    def get_all_feedback_ids(
        self, db: Optional[Session] = None
    ) -> list[FeedbackIdResponse]:
        with get_db_context(db) as db:
            return [
                FeedbackIdResponse(
                    id=row.id,
                    user_id=row.user_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in db.query(
                    Feedback.id,
                    Feedback.user_id,
                    Feedback.created_at,
                    Feedback.updated_at,
                )
                .order_by(Feedback.updated_at.desc())
                .all()
            ]

    def get_feedbacks_for_leaderboard(
        self, db: Optional[Session] = None
    ) -> list[LeaderboardFeedbackData]:
        """Fetch only id and data for leaderboard computation (excludes snapshot/meta)."""
        with get_db_context(db) as db:
            return [
                LeaderboardFeedbackData(id=row.id, data=row.data)
                for row in db.query(Feedback.id, Feedback.data).all()
            ]

    def get_model_evaluation_history(
        self, model_id: str, days: int = 30, db: Optional[Session] = None
    ) -> list[ModelHistoryEntry]:
        """
        Get daily wins/losses for a specific model over the past N days.
        If days=0, returns all time data starting from first feedback.
        Returns: [{"date": "2026-01-08", "won": 5, "lost": 2}, ...]
        """
        from datetime import datetime, timedelta
        from collections import defaultdict

        with get_db_context(db) as db:
            if days == 0:
                # All time - no cutoff
                rows = db.query(Feedback.created_at, Feedback.data).all()
            else:
                cutoff = int(time.time()) - (days * 86400)
                rows = (
                    db.query(Feedback.created_at, Feedback.data)
                    .filter(Feedback.created_at >= cutoff)
                    .all()
                )

        daily_counts = defaultdict(lambda: {"won": 0, "lost": 0})
        first_date = None

        for created_at, data in rows:
            if not data:
                continue
            if data.get("model_id") != model_id:
                continue

            rating_str = str(data.get("rating", ""))
            if rating_str not in ("1", "-1"):
                continue

            date_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d")
            if rating_str == "1":
                daily_counts[date_str]["won"] += 1
            else:
                daily_counts[date_str]["lost"] += 1

            # Track first date for this model
            if first_date is None or date_str < first_date:
                first_date = date_str

        # Generate date range
        result = []
        today = datetime.now().date()

        if days == 0 and first_date:
            # All time: start from first feedback date
            start_date = datetime.strptime(first_date, "%Y-%m-%d").date()
            num_days = (today - start_date).days + 1
        else:
            # Fixed range
            num_days = days
            start_date = today - timedelta(days=days - 1)

        for i in range(num_days):
            d = start_date + timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            counts = daily_counts.get(date_str, {"won": 0, "lost": 0})
            result.append(
                ModelHistoryEntry(date=date_str, won=counts["won"], lost=counts["lost"])
            )

        return result

    def get_feedbacks_by_type(
        self, type: str, db: Optional[Session] = None
    ) -> list[FeedbackModel]:
        with get_db_context(db) as db:
            return [
                FeedbackModel.model_validate(feedback)
                for feedback in db.query(Feedback)
                .filter_by(type=type)
                .order_by(Feedback.updated_at.desc())
                .all()
            ]

    def get_feedbacks_by_user_id(
        self, user_id: str, db: Optional[Session] = None
    ) -> list[FeedbackModel]:
        with get_db_context(db) as db:
            return [
                FeedbackModel.model_validate(feedback)
                for feedback in db.query(Feedback)
                .filter_by(user_id=user_id)
                .order_by(Feedback.updated_at.desc())
                .all()
            ]

    def update_feedback_by_id(
        self, id: str, form_data: FeedbackForm, db: Optional[Session] = None
    ) -> Optional[FeedbackModel]:
        with get_db_context(db) as db:
            feedback = db.query(Feedback).filter_by(id=id).first()
            if not feedback:
                return None

            if form_data.data:
                feedback.data = form_data.data.model_dump()
            if form_data.meta:
                feedback.meta = form_data.meta
            if form_data.snapshot:
                feedback.snapshot = form_data.snapshot.model_dump()

            feedback.updated_at = int(time.time())

            db.commit()
            return FeedbackModel.model_validate(feedback)

    def update_feedback_by_id_and_user_id(
        self,
        id: str,
        user_id: str,
        form_data: FeedbackForm,
        db: Optional[Session] = None,
    ) -> Optional[FeedbackModel]:
        with get_db_context(db) as db:
            feedback = db.query(Feedback).filter_by(id=id, user_id=user_id).first()
            if not feedback:
                return None

            if form_data.data:
                feedback.data = form_data.data.model_dump()
            if form_data.meta:
                feedback.meta = form_data.meta
            if form_data.snapshot:
                feedback.snapshot = form_data.snapshot.model_dump()

            feedback.updated_at = int(time.time())

            db.commit()
            return FeedbackModel.model_validate(feedback)

    def delete_feedback_by_id(self, id: str, db: Optional[Session] = None) -> bool:
        with get_db_context(db) as db:
            feedback = db.query(Feedback).filter_by(id=id).first()
            if not feedback:
                return False
            db.delete(feedback)
            db.commit()
            return True

    # TODO: Renesas
    def get_feedbacks_by_chat_id(self, chat_id: str, db: Optional[Session] = None) -> list[FeedbackModel]:
        with get_db_context(db) as db:
            return [
                FeedbackModel.model_validate(feedback)
                for feedback in db.query(Feedback)
                .filter_by(chat_id=chat_id)
                .order_by(Feedback.updated_at.desc())
                .all()
            ]

    def delete_feedback_by_id_and_user_id(
        self, id: str, user_id: str, db: Optional[Session] = None
    ) -> bool:
        with get_db_context(db) as db:
            feedback = db.query(Feedback).filter_by(id=id, user_id=user_id).first()
            if not feedback:
                return False
            db.delete(feedback)
            db.commit()
            return True

    def delete_feedbacks_by_user_id(
        self, user_id: str, db: Optional[Session] = None
    ) -> bool:
        with get_db_context(db) as db:
            feedbacks = db.query(Feedback).filter_by(user_id=user_id).all()
            if not feedbacks:
                return False
            for feedback in feedbacks:
                db.delete(feedback)
            db.commit()
            return True

    def delete_all_feedbacks(self, db: Optional[Session] = None) -> bool:
        with get_db_context(db) as db:
            feedbacks = db.query(Feedback).all()
            if not feedbacks:
                return False
            for feedback in feedbacks:
                db.delete(feedback)
            db.commit()
            return True


Feedbacks = FeedbackTable()
