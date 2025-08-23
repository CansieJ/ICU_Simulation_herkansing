from mesa import Agent
import numpy as np
from typing import Callable

class Home(Agent):
    def __init__(self, model, create_agent: Callable) -> None:
        super().__init__(model)
        self.create_agent = create_agent
        self.current_day = -1
        self.spawn_timestamps = []

    def step(self) -> None:
        if(self.model.clock.day_index is not self.current_day):
            
            self.current_day = self.model.clock.day_index
            percentage = self.model.datamanager.get_amount_percentage_by_day(self.current_day, False)
            amount_of_agents_today = int(self.model.amount * percentage)
            if(self.model.use_ic_spike):
                amount_of_agents_today += self.model.datamanager.get_icu_spike_by_day((self.model.clock.year - 25) * 365 + self.model.clock.day_index)
            
            self.spawn_timestamps = np.sort(self.model.get_normally_distributed_timestamps(amount_of_agents_today, False))
            self.model.datacollector.add_table_row("amount", { "date": self.model.clock.get_time(True), "admissions": len(self.spawn_timestamps) + len(self.model.agent_schedules[self.current_day]) })
        
        if(len(self.spawn_timestamps) > 0):
            current_timestamp = self.spawn_timestamps[0]
            
            if(self.model.clock.get_day_timestamp() >= current_timestamp):
                # Unplanned
                self.create_agent(False)
                self.spawn_timestamps = np.delete(self.spawn_timestamps, 0)

        if(len(self.model.agent_schedules[self.current_day]) > 0):
            current_timestamp = self.model.agent_schedules[self.current_day][0]
            
            if(self.model.clock.get_day_timestamp() >= current_timestamp):
                # Planned agent
                self.create_agent(True)
                self.model.agent_schedules[self.current_day] = np.delete(self.model.agent_schedules[self.current_day], 0)

        return super().step()
        