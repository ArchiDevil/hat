from pathlib import Path
from quart import Blueprint, current_app


bp = Blueprint("app", __name__)


def get_instance_path():
    instance_path = Path(current_app.instance_path)
    if not instance_path.exists():
        instance_path.mkdir(parents=True)
    return instance_path


@bp.route("/")
async def index():
    return "Index page (you should not see this!)"
