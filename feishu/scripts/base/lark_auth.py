import os
import time
import json
import requests
import lark_oapi as lark
from dotenv import load_dotenv
from pathlib import Path


class LarkAuth:
    """飞书认证管理类，负责提供 client 和 tenant_access_token(单例模式)"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """单例模式：确保只创建一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, app_id=None, app_secret=None, base_url=None):
        """
        初始化认证管理器

        :param app_id: 飞书应用ID，如果不提供则从环境变量读取
        :param app_secret: 飞书应用密钥，如果不提供则从环境变量读取
        :param base_url: 飞书API基础URL
        """
        # 单例模式：只初始化一次
        if LarkAuth._initialized:
            return

        result = load_dotenv()
        self._app_id = app_id or os.getenv("FEISHU_APP_ID")
        self._app_secret = app_secret or os.getenv("FEISHU_APP_SECRET")
        self._base_url = base_url or os.getenv(
            "BASE_URL", "https://open.feishu.cn/open-apis"
        )

        if not result or not self._app_id or not self._app_secret:
            raise EnvironmentError(
                """
                ❌ 错误：未找到飞书应用凭证, 请访问 https://open.feishu.cn/获取应用凭证
                在技能目录下创建 .env 文件, 并设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET
                可参考 .env.example 文件
                """
            )

        self._client = (
            lark.Client.builder()
            .app_id(self._app_id)
            .app_secret(self._app_secret)
            .log_level(lark.LogLevel.INFO)
            .build()
        )

        LarkAuth._initialized = True

    @classmethod
    def reset(cls):
        """
        重置单例（主要用于测试）

        警告：谨慎使用，会导致所有引用到该单例的代码失去一致性
        """
        cls._instance = None
        cls._initialized = False

    def get_client(self) -> lark.Client:
        """
        获取 lark client 实例

        :return: lark.Client 实例
        """
        return self._client

    def get_tenant_access_token(self) -> str | None:
        """
        获取 Tenant Access Token（应用级访问令牌）
        带缓存机制，自动处理过期

        :return: tenant_access_token 字符串
        """
        token_file = Path(__file__).parent / ".data" / ".tenant_access_token.json"
        api_url = self._base_url + "/auth/v3/tenant_access_token/internal"

        # 尝试从缓存读取token
        if token_file.exists():
            try:
                with open(token_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    token = cache_data.get("tenant_access_token")
                    expire = cache_data.get("expire", 0)
            except Exception as e:
                print(f"读取token失败: {e}")
                token = None
                expire = 0
        else:
            token = None
            expire = 0

        # 缓存未过期，直接返回
        if token and time.time() < expire:
            return token

        # 缓存过期或不存在，重新获取
        response = requests.post(
            api_url, json={"app_id": self._app_id, "app_secret": self._app_secret}
        )
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 0:
            raise ValueError(result)

        token = result.get("tenant_access_token")
        expire = result.get("expire", 0)

        if token is None:
            raise ValueError(result)

        # 保存token到缓存
        try:
            token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(token_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "tenant_access_token": token,
                        "expire": int(time.time()) + expire - 10,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            print(f"保存token失败: {e}")
            return None

        return token

    def get_base_url(self):
        return self._base_url
