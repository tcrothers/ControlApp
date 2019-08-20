from instruments.generic import BaseInstrumentGroup
from instruments.newport_xps import XpsGroup
from resources.web_connections import ConnectionManager

mock_user = {"username": "Tim"}

fake_xps = XpsGroup("Laura's XPS", ConnectionManager(), "172.0.0.0", 5001)

fake_xps.add_instrument("GROUP1")
fake_xps.add_instrument("GROUP2")
fake_xps.add_instrument("GROUP3")
fake_xps.add_instrument("GROUP4")

# todo: Should really prepend the group name on this to make unique
all_insts = BaseInstrumentGroup('all instruments')
all_insts.instruments.update(fake_xps.instruments)

# stage1 = NewStage("GROUP1")
# stage2 = NewStage("GROUP2")
# stage3 = NewStage("GROUP3")
# stage4 = NewStage("GROUP4")

# stages = {"GROUP1": stage1, "GROUP2": stage2,
#           "GROUP3": stage3, "GROUP4": stage4}
