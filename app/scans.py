from app.forms import AddStepForm, RemoveStepForm


class Scan:
    dummy = 0
    steps = []

    def add_step(self, new_step: AddStepForm):
        txt = []
        txt.append(f"*" * 31 + "    STEP {self.dummy}  " + "*"*31)
        txt.append(f"group {new_step.instrument_name.data}:{new_step.adjust.data}")
        txt.append(f"doing {new_step.start_value.data}:{new_step.num_steps.data}:{new_step.fin_value.data}")
        txt.append("*" * 80)
        self.steps.append("\n".join(txt))
        for s in self.steps: print(s)
        self.dummy += 1

    def rm_step(self, target_step: RemoveStepForm):
        print("in rm_step scan function")
        del self.steps[int(target_step.step_number.data)]
        self.dummy -= 1