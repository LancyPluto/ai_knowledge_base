from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from schema.schema import CurrentUser
from core.config import settings
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from sqlmodel.ext.asyncio.session import AsyncSession
from core.database import get_session
from repository.user_repo import user_repo
import base64
import hashlib
import hmac
import secrets




# HTTPBearer：从请求头 Authorization: Bearer <token> 中解析 token
# auto_error=False：不自动抛错，交给 get_current_user 自己返回 401
_security = HTTPBearer(auto_error=False)

# 密码哈希使用 PBKDF2-HMAC-SHA256
# 迭代次数越高越安全，但计算越慢；这里取一个相对安全的默认值
_PBKDF2_ITERATIONS = 200_000


def create_access_token(*, user_id: str) -> str:
    """
    生成 JWT 访问令牌（Access Token）

    - sub: 用户唯一标识（user_id）
    - iat: 签发时间（Unix 时间戳）
    - exp: 过期时间（Unix 时间戳）
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)).timestamp()),
    }
    # 使用对称加密 HS256（JWT_ALG）对 payload 签名，签名密钥为 JWT_SECRET
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def hash_password(password: str) -> str:
    """
    对明文密码进行不可逆哈希并返回可存储字符串。

    存储格式：
    pbkdf2_sha256$<iterations>$<salt_b64>$<derived_key_b64>
    """
    # 每个用户生成独立随机盐，避免相同密码哈希结果相同
    salt = secrets.token_bytes(16)
    # PBKDF2 推导密钥（derived key），用于存储对比，不存明文
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return "pbkdf2_sha256$%d$%s$%s" % (
        _PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("utf-8"),
        base64.urlsafe_b64encode(dk).decode("utf-8"),
    )


def verify_password(password: str, hashed_password: str) -> bool:
    """
    校验明文密码是否与存储的哈希匹配。

    - 解析存储格式拿到 iterations、salt、expected_dk
    - 用同样的算法对输入 password 推导 candidate_dk
    - 使用恒定时间比较避免时序攻击
    """
    try:
        scheme, iterations_str, salt_b64, dk_b64 = hashed_password.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
        expected = base64.urlsafe_b64decode(dk_b64.encode("utf-8"))
    except Exception:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    db: AsyncSession = Depends(get_session),
) -> CurrentUser:
    """
    FastAPI 依赖：从请求中识别当前用户（企业级 JWT 鉴权核心）

    工作流程：
    1) 从 Authorization: Bearer <token> 取出 token
    2) 使用 JWT_SECRET + JWT_ALG 对 token 解码验签并校验 exp（过期时间）
    3) 从 payload 读取 sub（user_id）
    4) 查询数据库确认用户存在且未被禁用
    5) 返回 CurrentUser(id=...)
    """
    # 未携带 Authorization 头或 token 为空
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials
    try:
        # jwt.decode 会同时进行签名校验与 exp 过期校验
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # 企业惯例：sub 存放用户唯一标识
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # 查询用户表，防止 token 中的 user_id 指向不存在/已删除用户
    user = await user_repo.get_by_id(db, user_id=str(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # 用户被禁用则拒绝访问
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User disabled",
        )

    return CurrentUser(id=user.id)
