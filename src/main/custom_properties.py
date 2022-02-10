from homie.node.property.property_boolean import Property_Boolean
from homie.node.property.property_float import Property_Float
from homie.node.property.property_integer import Property_Integer


class Property_PM25(Property_Float):
    def __init__(
            self,
            node,
            id="pm25",
            name="PM 2.5",
            settable=False,
            retained=True,
            qos=1,
            unit="μg/m³",
            data_type=None,
            data_format=None,
            value=None,
            set_value=None,
            tags=[],
            meta={},
    ):
        super().__init__(
            node,
            id,
            name,
            settable,
            retained,
            qos,
            unit,
            data_type,
            data_format,
            value,
            set_value,
            tags,
            meta,
        )


class Property_WaterLevel(Property_Integer):
    def __init__(
            self,
            node,
            id="water",
            name="Water level",
            settable=False,
            retained=True,
            qos=1,
            unit="",
            data_type=None,
            data_format=None,
            value=None,
            set_value=None,
            tags=[],
            meta={},
    ):
        super().__init__(
            node,
            id,
            name,
            settable,
            retained,
            qos,
            unit,
            data_type,
            data_format,
            value,
            set_value,
            tags,
            meta,
        )


class Property_IsOn(Property_Boolean):
    def __init__(
            self,
            node,
            id="ison",
            name="Is on",
            settable=False,
            retained=True,
            qos=1,
            unit=None,
            data_type=None,
            data_format=None,
            value=None,
            set_value=None,
            tags=[],
            meta={},
    ):
        super().__init__(
            node,
            id,
            name,
            settable,
            retained,
            qos,
            unit,
            data_type,
            data_format,
            value,
            set_value,
            tags,
            meta,
        )
