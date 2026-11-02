"""Local account sessions for the research workspace."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import time
from contextvars import ContextVar
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from ..scientific.research_store import connect, initialize, now, one, uid

router = APIRouter(prefix="/api/auth", tags=["Account"])
COOKIE = "soilmate_session"
SESSION_SECONDS = 60 * 60 * 24 * 7
ITERATIONS = 600_000
CURRENT_USER = ContextVar("current_soilmate_user", default=None)


def current_user_id():
    user_id = CURRENT_USER.get()
    if not user_id:
        raise HTTPException(401, "请先登录")
    return user_id


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)


def init_auth(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
      created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS auth_sessions(
      token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
      csrf_token TEXT NOT NULL, expires_at INTEGER NOT NULL, created_at TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
    CREATE TABLE IF NOT EXISTS auth_attempts(
      key TEXT PRIMARY KEY, count INTEGER NOT NULL, window_start INTEGER NOT NULL);
    """)
    columns = {row[1] for row in con.execute("PRAGMA table_info(projects)")}
    if "owner_user_id" not in columns:
        con.execute("ALTER TABLE projects ADD COLUMN owner_user_id TEXT")
    con.execute("CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_user_id)")


def normal_email(value):
    email = value.strip().lower()
    if email.count("@") != 1 or not email.split("@", 1)[0] or "." not in email.split("@", 1)[1]:
        raise HTTPException(422, "请输入有效邮箱地址")
    return email


def password_hash(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, encoded):
    try:
        algo, rounds, salt, expected = encoded.split("$")
        if algo != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def token_hash(token):
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def session_for(request, con):
    token = request.cookies.get(COOKIE, "")
    if len(token) < 32:
        return None
    return one(con, """SELECT s.user_id,s.csrf_token,s.expires_at,u.email FROM auth_sessions s
                        JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?""",
               (token_hash(token), int(time.time())))


def issue_session(response, request, con, user):
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    con.execute("INSERT INTO auth_sessions VALUES(?,?,?,?,?)",
                (token_hash(token), user["id"], csrf, int(time.time()) + SESSION_SECONDS, now()))
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=request.url.scheme == "https", samesite="lax", path="/")
    return {"user": {"id": user["id"], "email": user["email"]}, "csrf_token": csrf}


def check_limit(con, key):
    row = one(con, "SELECT count,window_start FROM auth_attempts WHERE key=?", (key,))
    if row and int(time.time()) - row["window_start"] < 900 and row["count"] >= 8:
        raise HTTPException(429, "尝试次数过多，请稍后重试")


def failed_attempt(con, key):
    current = int(time.time())
    row = one(con, "SELECT count,window_start FROM auth_attempts WHERE key=?", (key,))
    if row and current - row["window_start"] < 900:
        con.execute("UPDATE auth_attempts SET count=count+1 WHERE key=?", (key,))
    else:
        con.execute("INSERT OR REPLACE INTO auth_attempts VALUES(?,?,?)", (key, 1, current))


@router.get("/status")
def status():
    """Tell the local login page whether the first account needs creating."""
    initialize()
    with connect() as con:
        init_auth(con)
        return {"has_accounts": one(con, "SELECT 1 AS present FROM users LIMIT 1") is not None}


@router.post("/register")
def register(payload: Credentials, request: Request, response: Response):
    initialize()
    email = normal_email(payload.email)
    with connect() as con:
        init_auth(con)
        if one(con, "SELECT id FROM users WHERE email=?", (email,)):
            raise HTTPException(409, "此邮箱已注册，请直接登录")
        first = one(con, "SELECT COUNT(*) AS n FROM users")["n"] == 0
        user = {"id": uid("user"), "email": email}
        try:
            con.execute("INSERT INTO users VALUES(?,?,?,?)", (user["id"], email, password_hash(payload.password), now()))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "此邮箱已注册，请直接登录")
        # The first local account takes ownership of the pre-account research records.
        if first:
            con.execute("UPDATE projects SET owner_user_id=? WHERE owner_user_id IS NULL", (user["id"],))
        return issue_session(response, request, con, user)


@router.post("/login")
def login(payload: Credentials, request: Request, response: Response):
    initialize()
    email = normal_email(payload.email)
    key = hashlib.sha256((email + "|" + (request.client.host if request.client else "unknown")).encode()).hexdigest()
    with connect() as con:
        init_auth(con)
        check_limit(con, key)
        user = one(con, "SELECT id,email,password_hash FROM users WHERE email=?", (email,))
        if not user or not verify_password(payload.password, user["password_hash"]):
            if not user and one(con, "SELECT 1 AS present FROM users LIMIT 1") is None:
                raise HTTPException(404, "尚无账号，请先点击“创建账号”")
            failed_attempt(con, key)
            # Commit the rate-limit counter before raising.
            con.commit()
            raise HTTPException(401, "邮箱或密码不正确")
        con.execute("DELETE FROM auth_attempts WHERE key=?", (key,))
        return issue_session(response, request, con, user)


@router.get("/me")
def me(request: Request):
    initialize()
    with connect() as con:
        init_auth(con)
        session = session_for(request, con)
        if not session:
            raise HTTPException(401, "请先登录")
        return {"user": {"id": session["user_id"], "email": session["email"]},
                "csrf_token": session["csrf_token"]}


@router.post("/logout")
def logout(request: Request, response: Response):
    initialize()
    with connect() as con:
        init_auth(con)
        session = session_for(request, con)
        if session:
            if not hmac.compare_digest(request.headers.get("X-CSRF-Token", ""), session["csrf_token"]):
                raise HTTPException(403, "请求校验失败")
            con.execute("DELETE FROM auth_sessions WHERE token_hash=?", (token_hash(request.cookies[COOKIE]),))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}
