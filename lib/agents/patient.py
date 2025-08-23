from mesa import Agent
import numpy as np
# from lib.utils import get_amount_percentage_by_day

class Patient(Agent): 
    def __init__(self, model, age: int, gender: str, planned: bool, spec: str, los_icu: float) -> None:
        super().__init__(model)
        self.sickness = np.random.rand()
        self.is_in_icu = False
        self.icu_department = None
        self.adm_icu = None
        self.age = age
        self.gender = gender
        self.planned = planned
        self.spec = spec
        self.los_icu = int(los_icu * (24 * 3600))
        self.backup_los_icu = los_icu
        

    def move(self, location: tuple[int, int]) -> None:
        # neighbors: Sequence[tuple[int, int]]  = self.model.space.get_neighborhood(self.pos, moore=False, include_center=True, radius=1)
        # closest = np.iinfo(int).max
        # target = None
        
        # for neighbor in neighbors:
        #     dx = pow(location[0] - neighbor[0], 2)
        #     dy = pow(location[1] - neighbor[1], 2) 

        #     distance = np.sqrt(dx + dy)
        #     if(distance < closest):
        #         closest = distance
        #         target = neighbor

        self.model.space.move_agent(self, location)
    
    def set_icu_department(self, department) -> None:
        self.icu_department = department

    def step(self) -> None:
        if(self.icu_department is not None):
            if(self.icu_department.pos == self.pos and not self.is_in_icu ):
                self.adm_icu = self.model.clock.get_time(True)
                self.is_in_icu = True

        if(not self.is_in_icu and self.icu_department is None):
            self.move(self.model.get_front_desk_location())
        elif(not self.is_in_icu and self.icu_department is not None): 
            self.move(self.icu_department.pos)

        if(self.is_in_icu):
            if(self.icu_department.is_specialized):
                self.los_icu -= self.model.clock.clock_speed + int(self.model.clock.clock_speed * self.model.efficiency)
            else:
                self.los_icu -= self.model.clock.clock_speed
                
        if(self.los_icu <= 0):
            if(self.icu_department == None):
                print("dit kan helemaal niet", self.los_icu, self.backup_los_icu)
            self.model.datacollector.add_table_row("admissions", { "ref_spec": self.spec, "adm_icu": self.adm_icu, "dis_icu": self.model.clock.get_time(True), "los_icu": self.backup_los_icu, "age": self.age, "gender": self.gender, "plan_adm": self.planned })
            self.icu_department.free_capacity(self)
            self.remove()
            self.model.space.remove_agent(self)
