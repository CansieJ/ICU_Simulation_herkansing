from mesa import Agent
from typing import List
import numpy as np

#TODO: Create allocating capacity functions
class Department(Agent):
    def __init__(self, model, specs: List[str], capacity: int = 32, is_specialized: bool = False) -> None:
        super().__init__(model)
        self.specs = specs
        self.patients = []
        self.capacity = capacity
        self.is_specialized = is_specialized
        self.current_capacity = capacity

        self.beds = {}
        self.allocate_capacity()

    def allocate_capacity (self):
        pandemic_capacity = int(self.model.pandemic_allocation_percentage * self.capacity)
        normal_capacity = self.capacity - pandemic_capacity

        for i in range(normal_capacity):
            self.beds[i] = {
                "type": "normal",
                "patient": None
            }

        for i in range(pandemic_capacity):
            self.beds[i] = {
                "type": "pandemic",
                "patient": None
            }

    # def update_capacity (self):
    #     self.patients = [x for x in self.model.space.get_cell_list_contents([self.pos]) if type(x) != Department and x not in [v["patient"] for v in self.beds.values()]]

    #     for patient in self.patients:
            

        

    def free_capacity (self, patient):
        for key in self.beds.keys():
            if self.beds[key]["patient"] == patient:
                self.beds[key]["patient"] = None

    def allocate_patient_location (self, patient) -> None:
        choices = [key for key in self.beds.keys() if self.beds[key]["patient"] == None]
            
        key = (self.model.random.choice(choices)) #TODO: add condition for when self.beds[key]["type"] equals patient.type (which can either be normal or pandemic)
        self.beds[key]["patient"] = patient

    def step(self) -> None:
        self.current_capacity = len([x for x in self.beds.values() if x["patient"] == None])
        # self.update_capacity()
        return super().step()