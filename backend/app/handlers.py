from __future__ import annotations

import json

from .crud import CrudService
from .database import get_session
from .models import Customer


CUSTOMER_SERVICE = CrudService(Customer)


def read_customer(event, _context):
    customer_id = event.get("pathParameters", {}).get("id")
    user_id = event.get("requestContext", {}).get("identity", {}).get("user")
    with get_session() as session:
        result = CUSTOMER_SERVICE.read(session, record_id=customer_id, user_id=user_id)
        payload = {
            "data_log": {
                "is_success": result.data_log.is_success,
                "message": result.data_log.message,
            },
            "record": None,
        }
        if result.record:
            payload["record"] = {
                "id": str(result.record.id),
                "first_name": result.record.first_name,
                "last_name": result.record.last_name,
            }
        return {"statusCode": 200, "body": json.dumps(payload)}
