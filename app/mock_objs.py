from app.instruments import Stage

mock_user = {"username": "Tim"}

mock_stage1 = {"name": "Group1",
               "position": 45,
               "state": 12}

mock_stage2 = {"name": "Group2",
               "position": 100,
               "state": 12}

mock_xps = {"host": "172.16.0.0"}


stage1 = Stage("GROUP1")
stage2 = Stage("GROUP2")
stage3 = Stage("GROUP3")
stage4 = Stage("GROUP4")

mock_stages = {"GROUP1":stage1, "GROUP2":stage2,
               "GROUP3":stage3, "GROUP4":stage4}