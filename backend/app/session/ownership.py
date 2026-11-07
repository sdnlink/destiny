"""会话归属校验（审计 22）。

这里不做账号体系，只解决一个具体问题：同一套部署里，客户端 A 不应该能
读、排盘、交互或删除客户端 B 的会话，而此前的会话端点只按 `session_id` 直取。

机制：
1. 客户端首次运行生成一个 ≥16 位的随机 id（`localStorage`），每个会话请求都带
   `X-Client-Id` 头；
2. 服务端只存该 id 的 sha256（`owner_hash`），原始 id 不落盘；
3. 迁移前就已存在的会话没有 `owner_hash`，采用「首访问认领」：第一个带合法 id
   访问它的客户端成为其 owner，之后其他 id 一律 403。

为什么不是 bearer token：`APP_API_TOKEN` 是部署级口令，所有客户端共用同一个；
它能挡住"外人访问这套服务"，挡不住"同一部署里两个用户的会话互读"。两者互补。
"""

import hashlib
import re
from typing import Optional

from .models import DivinationSession


HEADER_NAME = "X-Client-Id"

# 客户端 id 由前端生成：32 位十六进制。放宽到 16–64 位 URL 安全字符，
# 但拒绝空白、斜杠与其它会被当成路径或正则元字符的输入。
CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def client_id_from(raw_header: Optional[str]) -> Optional[str]:
    """从请求头取值并校验；缺失或格式不合法都返回 None。"""
    if not isinstance(raw_header, str):
        return None
    value = raw_header.strip()
    if not CLIENT_ID_PATTERN.match(value):
        return None
    return value


def owner_hash(client_id: str) -> str:
    """只存哈希：即使会话文件被读走，也拿不到别的客户端的 id 去冒充。"""
    return "sha256:" + hashlib.sha256(client_id.encode("utf-8")).hexdigest()


def claim_or_match(session: DivinationSession, requested_owner: str) -> bool:
    """归属校验。

    - 会话尚无 owner（迁移前的老会话）：把 owner 认领给它，返回 True，
      调用方负责保存；
    - owner 一致：返回 True；
    - owner 不一致：返回 False，调用方应回 403。
    """
    if not session.owner_hash:
        session.owner_hash = requested_owner
        return True
    return session.owner_hash == requested_owner
