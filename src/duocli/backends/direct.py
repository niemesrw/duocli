from __future__ import annotations

from datetime import datetime, timezone

import duo_client

from .base import DuoBackend


class DirectBackend(DuoBackend):
    """Backend that calls the Duo Admin API directly using env-var credentials."""

    def __init__(self, ikey: str, skey: str, host: str) -> None:
        self._admin = duo_client.Admin(ikey=ikey, skey=skey, host=host)

    def create_integration(self, name: str, integration_type: str, **kwargs) -> dict:
        try:
            result = self._admin.create_integration(
                name=name, integration_type=integration_type, **kwargs
            )
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {
            "status": "ok",
            "integration_key": result.get("integration_key", ""),
            "secret_key": result.get("secret_key", ""),
            "name": result.get("name", ""),
            "type": result.get("type", ""),
        }

    def delete_integration(self, integration_key: str) -> dict:
        try:
            self._admin.delete_integration(integration_key)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {"status": "ok", "integration_key": integration_key}

    def list_integrations(self) -> list[dict]:
        try:
            results = self._admin.get_integrations()
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return [
            {
                "integration_key": r.get("integration_key", ""),
                "name": r.get("name", ""),
                "type": r.get("type", ""),
            }
            for r in results
        ]

    def get_integration(self, integration_key: str) -> dict:
        try:
            result = self._admin.get_integration(integration_key)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {
            "integration_key": result.get("integration_key", ""),
            "name": result.get("name", ""),
            "type": result.get("type", ""),
            "status": result.get("status", ""),
            "policy_key": result.get("policy_key", ""),
            "notes": result.get("notes", ""),
            "enroll_policy": result.get("enroll_policy", ""),
            "groups_allowed": result.get("groups_allowed", []),
        }

    def get_info_summary(self) -> dict:
        try:
            result = self._admin.get_info_summary()
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return result

    def get_authentication_logs(
        self, mintime: int, maxtime: int, **kwargs
    ) -> list[dict]:
        try:
            response = self._admin.get_authentication_log(
                api_version=2, mintime=mintime, maxtime=maxtime, **kwargs
            )
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return [
            {
                "timestamp": _format_ts_ms(row.get("timestamp")),
                "user": row.get("user", {}).get("name", ""),
                "result": row.get("result", ""),
                "reason": row.get("reason", ""),
                "factor": row.get("factor", ""),
                "application": row.get("application", {}).get("name", ""),
                "ip": row.get("access_device", {}).get("ip", ""),
            }
            for row in response.get("authlogs", [])
        ]

    def get_auth_stats(self, mintime: int, maxtime: int) -> dict:
        try:
            result = self._admin.get_authentication_attempts(
                mintime=str(mintime), maxtime=str(maxtime)
            )
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        attempts = result.get("authentication_attempts", result)
        return {k.lower(): v for k, v in attempts.items()}

    def list_policies(self) -> list[dict]:
        try:
            results = self._admin.get_policies_v2()
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return [
            {
                "policy_key": p.get("policy_key", ""),
                "name": p.get("policy_name", ""),
                "enabled": p.get("enabled", False),
            }
            for p in results
        ]

    def get_policy(self, policy_key: str) -> dict:
        try:
            result = self._admin.get_policy_v2(policy_key)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return result

    def update_integration(self, integration_key: str, **kwargs) -> dict:
        try:
            result = self._admin.update_integration(integration_key, **kwargs)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {
            "status": "ok",
            "integration_key": result.get("integration_key", ""),
            "name": result.get("name", ""),
            "type": result.get("type", ""),
        }

    def get_user(self, username: str | None = None, user_id: str | None = None) -> dict:
        try:
            if user_id:
                result = self._admin.get_user_by_id(user_id)
            else:
                results = self._admin.get_users_by_name(username)
                if not results:
                    return {"status": "error", "message": f"No user found with username: {username}", "code": 40400}
                result = results[0]
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {
            "user_id": result.get("user_id", ""),
            "username": result.get("username", ""),
            "email": result.get("email", ""),
            "realname": result.get("realname", ""),
            "status": result.get("status", ""),
            "is_enrolled": result.get("is_enrolled", False),
            "last_login": _format_ts_sec(result.get("last_login")),
            "phones_count": len(result.get("phones", [])),
            "groups_count": len(result.get("groups", [])),
            "notes": result.get("notes", ""),
        }

    def get_user_groups(self, user_id: str) -> list[dict]:
        try:
            results = self._admin.get_user_groups(user_id)
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return [
            {
                "group_id": g.get("group_id", ""),
                "name": g.get("name", ""),
                "description": g.get("desc", ""),
                "status": g.get("status", ""),
            }
            for g in results
        ]

    def get_user_devices(self, user_id: str) -> dict:
        try:
            phones = self._admin.get_user_phones(user_id)
            tokens = self._admin.get_user_tokens(user_id)
            webauthn = self._admin.get_user_webauthncredentials(user_id)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        phone_list = [
            {
                "type": "phone",
                "device_id": p.get("phone_id", ""),
                "name": p.get("name", ""),
                "number": p.get("number", ""),
                "platform": p.get("platform", ""),
                "activated": p.get("activated", False),
            }
            for p in phones
        ]
        token_list = [
            {
                "type": "token",
                "device_id": t.get("token_id", ""),
                "serial": t.get("serial", ""),
                "token_type": t.get("type", ""),
            }
            for t in tokens
        ]
        webauthn_list = [
            {
                "type": "webauthn",
                "credential_name": w.get("credential_name", ""),
                "date_added": _format_ts_sec(w.get("date_added")),
                "label": w.get("label", ""),
            }
            for w in webauthn
        ]
        all_devices = phone_list + token_list + webauthn_list
        return {
            "user_id": user_id,
            "phones": phone_list,
            "tokens": token_list,
            "webauthn": webauthn_list,
            "total_devices": len(all_devices),
        }

    def calculate_policy(self, integration_key: str, user_id: str) -> dict:
        try:
            result = self._admin.calculate_policy(integration_key, user_id)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return result

    def enroll_user(self, username: str, email: str, valid_secs: int | None = None) -> dict:
        try:
            kwargs = {"username": username, "email": email}
            if valid_secs is not None:
                kwargs["valid_secs"] = valid_secs
            result = self._admin.enroll_user(**kwargs)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        # API returns a string (enrollment code) or a dict with enrollment_url
        if isinstance(result, dict):
            enrollment_code = result.get("enrollment_code", "")
            enrollment_url = result.get("enrollment_url", "")
        else:
            enrollment_code = str(result) if result else ""
            enrollment_url = ""
        return {
            "status": "ok",
            "username": username,
            "email": email,
            "enrollment_code": enrollment_code,
            "enrollment_url": enrollment_url,
        }

    def send_sms_activation(self, user_id: str, valid_secs: int | None = None) -> dict:
        try:
            phones = self._admin.get_user_phones(user_id)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        if not phones:
            return {
                "status": "error",
                "message": f"User {user_id} has no phones — add a phone before sending SMS activation",
                "code": 40400,
            }
        phone = phones[0]
        phone_id = phone.get("phone_id", "")
        try:
            kwargs: dict = {"install": 1}
            if valid_secs is not None:
                kwargs["valid_secs"] = valid_secs
            result = self._admin.send_sms_activation_to_phone(phone_id, **kwargs)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {
            "status": "ok",
            "user_id": user_id,
            "phone_id": phone_id,
            "number": phone.get("number", ""),
            "activation_msg": result.get("activation_msg", "") if isinstance(result, dict) else "",
            "installation_msg": result.get("installation_msg", "") if isinstance(result, dict) else "",
            "valid_secs": result.get("valid_secs", "") if isinstance(result, dict) else "",
        }

    def get_activity_logs(
        self, mintime: int, maxtime: int, limit: int = 500,
    ) -> list[dict]:
        try:
            events = []
            kwargs = {"mintime": str(mintime), "maxtime": str(maxtime)}
            while len(events) < limit:
                response = self._admin.get_activity_logs(**kwargs)
                items = response.get("items", [])
                if not items:
                    break
                for item in items:
                    if len(events) >= limit:
                        break
                    events.append({
                        "timestamp": item.get("ts", ""),
                        "action": (item.get("action") or {}).get("name", ""),
                        "actor": (item.get("actor") or {}).get("name", ""),
                        "actor_type": (item.get("actor") or {}).get("type", ""),
                        "target": (item.get("target") or {}).get("name", ""),
                        "target_type": (item.get("target") or {}).get("type", ""),
                        "application": (item.get("application") or {}).get("name", ""),
                        "ip": (item.get("access_device") or {}).get("ip") or "",
                    })
                next_offset = response.get("metadata", {}).get("next_offset")
                if not next_offset:
                    break
                kwargs["next_offset"] = next_offset
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return events

    def get_trust_monitor_events(
        self, mintime: int, maxtime: int, limit: int = 500,
    ) -> list[dict]:
        try:
            events = []
            for event in self._admin.get_trust_monitor_events_iterator(
                mintime=mintime, maxtime=maxtime,
            ):
                events.append({
                    "timestamp": event.get("surfaced_timestamp", ""),
                    "type": event.get("type", ""),
                    "priority": event.get("priority", ""),
                    "description": event.get("triage_event_uri", ""),
                    "from_common_netblock": event.get("from_common_netblock", ""),
                    "sekey": event.get("sekey", ""),
                })
                if len(events) >= limit:
                    break
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return events

    def get_administrator_logs(self, mintime: int) -> list[dict]:
        try:
            results = self._admin.get_administrator_log(mintime=mintime)
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return [
            {
                "timestamp": _format_ts_sec(row.get("timestamp")),
                "admin": row.get("username", ""),
                "action": row.get("action", ""),
                "object": row.get("object", ""),
                "description": row.get("description", ""),
            }
            for row in results
        ]


def _format_ts_ms(ts) -> str:
    """Format a millisecond unix timestamp to ISO 8601."""
    if ts is None:
        return ""
    return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).isoformat()


def _format_ts_sec(ts) -> str:
    """Format a second unix timestamp to ISO 8601."""
    if ts is None:
        return ""
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
