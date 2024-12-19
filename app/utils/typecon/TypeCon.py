import datetime
import json
from decimal import Decimal
from typing import Any
import arrow
import pendulum
import pandas as pd
import dateutil.parser
import pytz
from zoneinfo import ZoneInfo


class TypeCon:
    @staticmethod
    def convert(value: Any, target_type: str, default: Any = None) -> Any:
        converters = {
            "str": [lambda x: str(x), lambda x: json.dumps(x), lambda x: repr(x)],
            "int": [
                lambda x: int(x),
                lambda x: int(float(x)),
                lambda x: int(Decimal(str(x))),
            ],
            "float": [
                lambda x: float(x),
                lambda x: float(Decimal(str(x))),
                lambda x: float(str(x).replace(",", ".")),
            ],
            "bool": [
                lambda x: bool(x),
                lambda x: str(x).lower() in ("true", "1", "yes", "y", "on"),
                lambda x: int(x) != 0,
            ],
            "list": [
                lambda x: list(x),
                lambda x: json.loads(x) if isinstance(x, str) else [x],
                lambda x: [x] if not hasattr(x, "__iter__") else list(x),
            ],
            "dict": [
                lambda x: dict(x),
                lambda x: json.loads(x) if isinstance(x, str) else {"value": x},
                lambda x: (
                    {str(k): v for k, v in x.items()}
                    if hasattr(x, "items")
                    else {"value": x}
                ),
            ],
            "datetime": [
                # Standard datetime
                lambda x: datetime.datetime.fromisoformat(x),
                lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S"),
                lambda x: datetime.datetime.fromtimestamp(float(x)),
                # Arrow
                lambda x: arrow.get(x).datetime,
                lambda x: arrow.Arrow.strptime(x, "%Y-%m-%d %H:%M:%S").datetime,
                lambda x: arrow.Arrow.fromtimestamp(float(x)).datetime,
                # Pendulum
                lambda x: pendulum.parse(x).in_timezone("UTC").datetime(),
                lambda x: pendulum.from_format(x, "YYYY-MM-DD HH:mm:ss").datetime(),
                lambda x: pendulum.from_timestamp(float(x)).datetime(),
                # Pandas
                lambda x: pd.to_datetime(x).to_pydatetime(),
                lambda x: pd.Timestamp(x).to_pydatetime(),
                # DateUtil
                lambda x: dateutil.parser.parse(x),
                lambda x: dateutil.parser.isoparse(x),
            ],
            "date": [
                # Standard date
                lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").date(),
                lambda x: datetime.date.fromisoformat(x),
                lambda x: datetime.datetime.fromtimestamp(float(x)).date(),
                # Arrow
                lambda x: arrow.get(x).date(),
                lambda x: arrow.Arrow.strptime(x, "%Y-%m-%d").date(),
                # Pendulum
                lambda x: pendulum.parse(x).date(),
                lambda x: pendulum.from_format(x, "YYYY-MM-DD").date(),
                # Pandas
                lambda x: pd.to_datetime(x).date(),
                lambda x: pd.Timestamp(x).date(),
                # DateUtil
                lambda x: dateutil.parser.parse(x).date(),
            ],
            "time": [
                # Standard time
                lambda x: datetime.datetime.strptime(x, "%H:%M:%S").time(),
                lambda x: datetime.time.fromisoformat(x),
                # Arrow
                lambda x: arrow.get(x).time(),
                lambda x: arrow.Arrow.strptime(x, "%H:%M:%S").time(),
                # Pendulum
                lambda x: pendulum.parse(x).time(),
                lambda x: pendulum.from_format(x, "HH:mm:ss").time(),
                # Pandas
                lambda x: pd.to_datetime(x).time(),
                lambda x: pd.Timestamp(x).time(),
            ],
            "timestamp": [
                # Unix timestamp conversions
                lambda x: datetime.datetime.fromtimestamp(float(x)),
                lambda x: arrow.get(float(x)).timestamp(),
                lambda x: pendulum.from_timestamp(float(x)).timestamp(),
                lambda x: pd.Timestamp(float(x), unit="s").timestamp(),
            ],
            "timezone": [
                # Timezone aware conversions
                lambda x: pytz.timezone(str(x)),
                lambda x: ZoneInfo(str(x)),
                lambda x: datetime.datetime.now(pytz.timezone(str(x))),
                lambda x: pendulum.timezone(str(x)),
            ],
            "decimal": [
                lambda x: Decimal(str(x)),
                lambda x: Decimal(str(x).replace(",", ".")),
                lambda x: Decimal(float(x)),
            ],
        }

        if target_type not in converters:
            return default

        for converter in converters[target_type]:
            try:
                result = converter(value)
                return result
            except (ValueError, TypeError, json.JSONDecodeError, AttributeError):
                continue

        return default
