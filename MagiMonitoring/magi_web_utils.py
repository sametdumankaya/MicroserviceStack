import random
import string
import os


def start_magi_web(magi_web_mysql_port: int, magi_web_ui_port: int):
    project_name = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    start_magi_web_code = os.system(
        f"cd MagiWeb/FinanceVisualization && "
        f"MYSQL_PORT={magi_web_mysql_port} "
        f"MAGI_WEB_PORT={magi_web_ui_port} "
        f"MYSQL_VOLUME_PATH={project_name} "
        f"docker-compose -p magifinance_{project_name} up -d")
    return project_name, start_magi_web_code


def kill_magi_web(project_name: str):
    kill_magi_web_code = os.system(
        f"cd MagiWeb/FinanceVisualization && "
        f"MYSQL_PORT=1111 "
        f"MAGI_WEB_PORT=1111 "
        f"MYSQL_VOLUME_PATH={project_name} "
        f"docker-compose -p magifinance_{project_name} down")
    return kill_magi_web_code
