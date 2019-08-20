from app.scans import Scan
from app.mock_objs import all_insts
import numpy as np
import trio

test_step_1 = ("GROUP1", "Position", np.array([1, 2, 3, 4, 5]))
test_step_2 = ("GROUP2", "Position", np.array([10, 20]))
test_meas_3 = ("GROUP3", "Position")

def new_scan():
    return Scan(all_insts)


def test_build_scan():
    print("*" * 10, "testing build scan", "*" * 10)
    my_scan = new_scan()
    print("scan built")
    print(f"scan._insts = {my_scan._insts}\n\n")


def test_add_steps():
    print("*" * 10, "testing add step", "*" * 10)
    my_scan = new_scan()
    my_scan.add_step(*test_step_1)
    my_scan.add_step(*test_step_2)
    print("steps added")
    print(f"scan has {len(my_scan.steps)} steps")

async def test_measure():
    print("*" * 10, "testing measure", "*" * 10)
    my_scan = new_scan()
    my_scan.add_step(*test_step_1)
    await all_insts.instruments['GROUP1'].set_param('Position', 1)
    val = await all_insts.instruments['GROUP1'].get_param('Position')
    print(val)
    print("using report method:")
    val = await my_scan.steps[0].measure()
    print(val)

def test_scanning():
    print("*" * 10, "testing scan", "*" * 10)
    my_scan = new_scan()
    my_scan.add_step(*test_step_1)
    my_scan.add_step(*test_step_2)
    my_scan.add_measurement(*test_meas_3)
    trio.run(my_scan.run, "test_scanning")
    print("scan finished successfully")

if __name__ == "__main__":
    test_build_scan()
    test_add_steps()
    trio.run(test_measure)
    test_scanning()
