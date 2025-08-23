from mesa import Agent
import numpy as np
from .patient import Patient

class Frontdesk(Agent):
    def __init__(self, model, pos: tuple[int, int], planning_method: int):
        super().__init__(model)
        self.row_pos = (pos[0], pos[1] - 1)
        self.planning_method = planning_method
        self.function_dict = {
            1: self.reschedule_patient_24,
            2: self.reschedule_patient_random,
            3: self.reschedule_patient_lowest
        }

    def step(self) -> None:
        in_front = [x for x in self.model.space.get_cell_list_contents([self.row_pos]) if type(x) == Patient]
        if len(in_front) > 0:
            patient: Patient = sorted(in_front, key=lambda a: a.unique_id)[0]
            if patient is not None:
                # Get the department based on the spec
                department = self.model.get_icu_department(patient.spec)

                if department is not None and department.current_capacity > 0:
                    # There is space, assign the patient to the department
                    department.allocate_patient_location(patient)
                    patient.set_icu_department(department)

                # No space
                else:
                    # Check if patient is planned
                    if patient.planned:
                        self.function_dict[self.planning_method](patient)
                        self.model.datacollector.add_table_row("replanning", {"date": self.model.clock.get_time(True), "planning_method": self.planning_method })
                    else:
                        self.model.datacollector.add_table_row("refused", { "ref_spec": patient.spec, "date": self.model.clock.get_time(True) })
                        self.deny_patient(patient)


    def reschedule_patient_24(self, patient: Patient):
        """Reschedule a planned patient for a day later."""
        patient.remove()
        self.model.space.remove_agent(patient)
        index = self.model.clock.day_index + 1
        if(self.model.clock.day_index + 1 > 365):
            index = 1       
        self.model.agent_schedules[index] = np.sort(
            np.concatenate((self.model.agent_schedules[index], [self.model.clock.get_day_timestamp()]))
        )

    def reschedule_patient_random(self, patient: Patient):
        """Reschedule a planned patient to a random future day within 1-2 weeks."""
        patient.remove()
        self.model.space.remove_agent(patient) 

        # Rescheduling takes place between a day and two weeks later
        min_day = self.model.clock.day_index + 1
        max_day = self.model.clock.day_index + 14  


        random_day = np.random.randint(min_day, max_day + 1)
        random_day = random_day if random_day <= 365 else random_day - 365

        self.model.agent_schedules[random_day] = np.sort(
            np.concatenate([self.model.agent_schedules[random_day], [self.model.clock.get_day_timestamp()]])
        )


    def reschedule_patient_lowest(self, patient: Patient):
        """Reschedule a planned patient to the day with the least planned appointments within the current week."""
        patient.remove()
        self.model.space.remove_agent(patient)

        current_week = range(self.model.clock.day_index, self.model.clock.day_index + 7)
        # Find the day with the least scheduled appointments
        min_day = min(current_week, key=lambda day: len(self.model.agent_schedules.get(day if day <= 365 else day - 365, [])))
        min_day = min_day if min_day <= 365 else min_day - 365
        self.model.agent_schedules[min_day] = np.sort(
            np.concatenate([self.model.agent_schedules[min_day], [self.model.clock.get_day_timestamp()]])
        )
        
    def deny_patient(self, patient: Patient):
        """Deny an unplanned patient and simulate redirection."""
        patient.remove()
        self.model.space.remove_agent(patient)  
