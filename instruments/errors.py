import json


class MovementException(Exception):
    def to_json(self):
        return json.dumps({"error": f'{self.args[0]}'})
