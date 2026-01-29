from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Generic, Iterable, TypeVar

from sqlalchemy import and_
from sqlalchemy.orm import Session

from .config import TABLE_CONFIGS, ColumnSpec
from .exceptions import RecordNotFound
from .models import DataAction, DataLog, Invoice

ModelType = TypeVar("ModelType")


@dataclass
class ReadResult(Generic[ModelType]):
    data_log: DataLog
    record: ModelType | None


@dataclass
class CrudResult:
    data_log: DataLog


@dataclass
class CreateDataLogResult:
    data_log: DataLog


def _utc_now():
    return datetime.now(timezone.utc)


def _has_is_active(model: type) -> bool:
    return hasattr(model, "is_active")


def _active_query(session: Session, model: type[ModelType]):
    query = session.query(model)
    if _has_is_active(model):
        return query.filter(model.is_active.is_(True))
    return query


def _normalize_action(value: str) -> str:
    return value.strip().lower()


def create_data_log(
    session: Session,
    *,
    data_action: str,
    is_success: bool,
    record_id: Any | None = None,
    message: str | None = None,
    detailed_log: str | None = None,
    user_id: str | None = None,
) -> CreateDataLogResult:
    lookup_value = _normalize_action(data_action)
    action = session.query(DataAction).filter(DataAction.lookup_value == lookup_value).one_or_none()
    if action is None:
        raise RecordNotFound(f"Could not find DataAction {data_action}.")

    data_log = DataLog(
        data_action_id=action.id,
        is_success=is_success,
        record_id=record_id,
        message=message,
        detailed_log=detailed_log,
        user_id=user_id,
        timestamp=_utc_now(),
    )
    session.add(data_log)
    session.flush()
    return CreateDataLogResult(data_log=data_log)


class CrudService(Generic[ModelType]):
    def __init__(self, model: type[ModelType]):
        self.model = model
        self.config = TABLE_CONFIGS[model]

    def read(self, session: Session, *, record_id: Any, user_id: str | None = None) -> ReadResult[ModelType]:
        try:
            record = _active_query(session, self.model).filter(self.model.id == record_id).one_or_none()
            if record is None:
                log_result = create_data_log(
                    session,
                    data_action="read",
                    is_success=False,
                    record_id=record_id,
                    message=f"{self.model.__name__} not found.",
                    detailed_log=f"{record_id} for {self.model.__name__} was not found",
                    user_id=user_id,
                )
                return ReadResult(data_log=log_result.data_log, record=None)

            log_result = create_data_log(
                session,
                data_action="read",
                is_success=True,
                record_id=record.id,
                message=f"{self.model.__name__} read.",
                user_id=user_id,
            )
            return ReadResult(data_log=log_result.data_log, record=record)
        except Exception as exc:
            log_result = create_data_log(
                session,
                data_action="read",
                is_success=False,
                record_id=record_id,
                message="An error has occurred.",
                detailed_log=str(exc),
                user_id=user_id,
            )
            return ReadResult(data_log=log_result.data_log, record=None)

    def validate(self, session: Session, *, source: ModelType, user_id: str | None = None) -> CrudResult:
        messages: list[str] = []
        try:
            for spec in self._column_specs():
                value = getattr(source, spec.name, None)
                if spec.required and value is None:
                    messages.append(f"{spec.name} is required.")
                    continue
                if spec.required and isinstance(value, str) and value.strip() == "":
                    messages.append(f"{spec.name} must contain at least one character.")
                    continue
                if isinstance(value, str) and spec.max_length is not None:
                    if len(value) > spec.max_length:
                        messages.append(f"{spec.name} must be at most {spec.max_length} characters.")
                if spec.min_value is not None or spec.max_value is not None:
                    if value is None:
                        continue
                    try:
                        numeric_value = Decimal(str(value))
                    except (InvalidOperation, ValueError):
                        messages.append(f"{spec.name} must be a number.")
                        continue
                    if spec.min_value is not None and numeric_value < spec.min_value:
                        messages.append(
                            f"{spec.name} must be greater than or equal to {spec.min_value}."
                        )
                    if spec.max_value is not None and numeric_value > spec.max_value:
                        messages.append(
                            f"{spec.name} must be less than or equal to {spec.max_value}."
                        )

            record_id = getattr(source, "id", None)
            if record_id:
                existing = _active_query(session, self.model).filter(self.model.id == record_id).one_or_none()
                if existing is None:
                    messages.append(f"{self.model.__name__} with Id {record_id} does not exist.")

            if messages:
                log_result = create_data_log(
                    session,
                    data_action="validate",
                    is_success=False,
                    record_id=record_id,
                    message=f"{self.model.__name__} failed validation.",
                    detailed_log="\n".join(messages),
                    user_id=user_id,
                )
                return CrudResult(data_log=log_result.data_log)

            log_result = create_data_log(
                session,
                data_action="validate",
                is_success=True,
                record_id=record_id,
                message=f"{self.model.__name__} validated.",
                detailed_log="",
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)
        except Exception as exc:
            log_result = create_data_log(
                session,
                data_action="validate",
                is_success=False,
                record_id=getattr(source, "id", None),
                message="An error has occurred.",
                detailed_log=str(exc),
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)

    def get_can_remove(
        self, session: Session, *, record_id: Any, user_id: str | None = None
    ) -> CrudResult:
        try:
            record = session.query(self.model).filter(self.model.id == record_id).one_or_none()
            if record is None:
                log_result = create_data_log(
                    session,
                    data_action="validate",
                    is_success=False,
                    record_id=record_id,
                    message=f"Record with Id {record_id} does not exist and cannot be removed.",
                    user_id=user_id,
                )
                return CrudResult(data_log=log_result.data_log)
            if _has_is_active(self.model) and record.is_active is False:
                log_result = create_data_log(
                    session,
                    data_action="validate",
                    is_success=False,
                    record_id=record_id,
                    message=f"Record with Id {record_id} has already been removed.",
                    user_id=user_id,
                )
                return CrudResult(data_log=log_result.data_log)

            log_result = create_data_log(
                session,
                data_action="validate",
                is_success=True,
                record_id=record_id,
                message=f"Record with Id {record_id} can be removed.",
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)
        except Exception as exc:
            log_result = create_data_log(
                session,
                data_action="validate",
                is_success=False,
                record_id=record_id,
                message="An error has occurred.",
                detailed_log=str(exc),
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)

    def get_can_delete(
        self, session: Session, *, record_id: Any, user_id: str | None = None
    ) -> CrudResult:
        messages: list[str] = []
        try:
            record = session.query(self.model).filter(self.model.id == record_id).one_or_none()
            if record is None:
                log_result = create_data_log(
                    session,
                    data_action="validate",
                    is_success=False,
                    record_id=record_id,
                    message=f"Record with Id {record_id} does not exist and cannot be deleted.",
                    user_id=user_id,
                )
                return CrudResult(data_log=log_result.data_log)

            for child_model in self.config["children"]:
                for child_record in self._find_children(session, child_model, record_id):
                    child_service = CrudService(child_model)
                    child_log = child_service.get_can_delete(
                        session,
                        record_id=child_record.id,
                        user_id=user_id,
                    ).data_log
                    if not child_log.is_success:
                        if child_log.message:
                            messages.append(child_log.message)

            if not messages:
                log_result = create_data_log(
                    session,
                    data_action="validate",
                    is_success=True,
                    record_id=record_id,
                    message=f"Record with Id {record_id} can be deleted.",
                    user_id=user_id,
                )
                return CrudResult(data_log=log_result.data_log)

            log_result = create_data_log(
                session,
                data_action="validate",
                is_success=False,
                record_id=record_id,
                message=f"Record with Id {record_id} cannot be deleted.",
                detailed_log="\n".join(messages),
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)
        except Exception as exc:
            log_result = create_data_log(
                session,
                data_action="validate",
                is_success=False,
                record_id=record_id,
                message="An error has occurred.",
                detailed_log=str(exc),
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)

    def upsert(self, session: Session, *, source: ModelType, user_id: str | None = None) -> CrudResult:
        try:
            validate_result = self.validate(session, source=source, user_id=user_id)
            if not validate_result.data_log.is_success:
                return validate_result

            if self.model is Invoice:
                total_due = Decimal(str(getattr(source, "total_amount_due")))
                total_paid = Decimal(str(getattr(source, "total_amount_paid")))
                setattr(source, "total_amount_due", total_due - total_paid)

            record_id = getattr(source, "id", None)
            if not record_id:
                if _has_is_active(self.model):
                    setattr(source, "is_active", True)
                session.add(source)
                session.flush()
                log_result = create_data_log(
                    session,
                    data_action="create",
                    is_success=True,
                    record_id=source.id,
                    message=f"{self.model.__name__} created.",
                    user_id=user_id,
                )
                return CrudResult(data_log=log_result.data_log)

            existing = session.query(self.model).filter(self.model.id == record_id).one()
            for spec in self._column_specs():
                setattr(existing, spec.name, getattr(source, spec.name))
            session.flush()
            log_result = create_data_log(
                session,
                data_action="update",
                is_success=True,
                record_id=record_id,
                message=f"{self.model.__name__} updated.",
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)
        except Exception as exc:
            action = "update" if getattr(source, "id", None) else "create"
            log_result = create_data_log(
                session,
                data_action=action,
                is_success=False,
                record_id=getattr(source, "id", None),
                message="An error has occurred.",
                detailed_log=str(exc),
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)

    def remove(self, session: Session, *, record_id: Any, user_id: str | None = None) -> CrudResult:
        try:
            can_remove = self.get_can_remove(session, record_id=record_id, user_id=user_id)
            if not can_remove.data_log.is_success:
                return can_remove

            record = session.query(self.model).filter(self.model.id == record_id).one()
            if _has_is_active(self.model):
                record.is_active = False
            session.flush()
            log_result = create_data_log(
                session,
                data_action="softdelete",
                is_success=True,
                record_id=record_id,
                message=f"{self.model.__name__} removed.",
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)
        except Exception as exc:
            log_result = create_data_log(
                session,
                data_action="softdelete",
                is_success=False,
                record_id=record_id,
                message="An error has occurred.",
                detailed_log=str(exc),
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)

    def delete(self, session: Session, *, record_id: Any, user_id: str | None = None) -> CrudResult:
        try:
            can_delete = self.get_can_delete(session, record_id=record_id, user_id=user_id)
            if not can_delete.data_log.is_success:
                return can_delete

            for child_model in self.config["children"]:
                for child_record in self._find_children(session, child_model, record_id):
                    child_service = CrudService(child_model)
                    child_result = child_service.delete(
                        session,
                        record_id=child_record.id,
                        user_id=user_id,
                    )
                    if not child_result.data_log.is_success:
                        return child_result

            record = session.query(self.model).filter(self.model.id == record_id).one()
            session.delete(record)
            session.flush()
            log_result = create_data_log(
                session,
                data_action="harddelete",
                is_success=True,
                record_id=record_id,
                message=f"{self.model.__name__} deleted.",
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)
        except Exception as exc:
            log_result = create_data_log(
                session,
                data_action="harddelete",
                is_success=False,
                record_id=record_id,
                message="An error has occurred.",
                detailed_log=str(exc),
                user_id=user_id,
            )
            return CrudResult(data_log=log_result.data_log)

    def _column_specs(self) -> Iterable[ColumnSpec]:
        return self.config["columns"]

    def _find_children(self, session: Session, child_model: type, parent_id: Any):
        fk_columns = [
            fk.parent
            for fk in child_model.__table__.foreign_keys
            if fk.column.table.name == self.model.__table__.name
        ]
        if not fk_columns:
            return []
        filters = [column == parent_id for column in fk_columns]
        return session.query(child_model).filter(and_(*filters)).all()
