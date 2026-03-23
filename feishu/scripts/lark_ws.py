import os
from dotenv import load_dotenv
from .wrapper import RobotWrapper
from .folder_manage import FileCollectorBot

load_dotenv()
APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")


def main():
    if not APP_ID or not APP_SECRET:
        raise EnvironmentError(
            "❌ 未找到 FEISHU_APP_ID 或 FEISHU_APP_SECRET, 请检查 .env 文件"
        )

    bot_info = RobotWrapper().get_bot_info()
    if not bot_info or not bot_info.open_id:
        raise EnvironmentError("❌ 未获取到机器人信息, 请检查是否启用了机器人")

    bot = FileCollectorBot(APP_ID, APP_SECRET, bot_info.open_id)
    bot.start()


if __name__ == "__main__":
    main()