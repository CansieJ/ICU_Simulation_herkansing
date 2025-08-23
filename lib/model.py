from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from lib.agents import Patient, Frontdesk, Department, Home

from lib.utils import Clock, DataManager
from typing import List
import numpy as np
import solara



class ICUModel(Model):
    def __init__(self, seed = None, size: int = 20, amount: int = 4500, clock_speed: int = 10, 
                 departments = solara.reactive([["CAPU", "CARD", "INT", "Other","CHIR", "NEC", "NEU"]]), 
                 distribution = solara.reactive([1]),
                 is_specialized = solara.reactive([False]),
                 planning_method: int = 1,
                 capacity: int = 32,
                 efficiency: int = 0,
                 pandemic_allocation_percentage: int = 0,
                 use_ic_spike: bool = False) -> None:
        super().__init__(seed=seed)

        if (seed is not None):
            np.random.seed(seed=seed)

        self.departments = departments
        if (len(self.departments.value) != len(distribution.value)):
            self.distribution = solara.reactive([1 / len(self.departments.value) for x in range(len(self.departments.value))])
        else:
            self.distribution = distribution
        if (len(self.departments.value) != len(is_specialized.value)):   
            self.is_specialized = solara.reactive([False for _ in range(len(self.departments.value))])
        else:
            self.is_specialized = is_specialized
        self.efficiency = efficiency / 100 if efficiency != 0 else 0
        self.pandemic_allocation_percentage = pandemic_allocation_percentage / 100 if pandemic_allocation_percentage != 0 else 0
        self.capacity = capacity
        self.use_ic_spike = use_ic_spike
        
        
        self.space = MultiGrid(size, size, torus=False)
        self.clock = Clock(clock_speed)
        self.datamanager = DataManager()
        self.datacollector = DataCollector(model_reporters={
            "Capacity": lambda m: sum([x.current_capacity for x in m.agents_by_type[Department]])
            # "Costs": lambda m: sum([x.capacity * 2500 / m.clock.seconds_in_day * m.clock.clock_speed for x in m.agents_by_type[Department]])
        },
        tables={
            "admissions": ["ref_spec", "adm_icu", "dis_icu", "los_icu", "age", "gender", "plan_adm"],
            "refused": ["date", "ref_spec"],
            "costs": ["date", "amount_empty_beds", "cumulative_hourly_costs", "cumulative_daily_costs"],
            "capacity": ["date"] + [", ".join(x) for x in self.departments.value],
            "amount": ["date", "admissions"],
            "replanning": ["date", "planning_method"]
        })

        self.amount = amount
        self.current_year = self.clock.year
        self.current_hour = self.clock.hour
        self.current_day = self.clock.day

        self.cumulative_hourly_costs = 0
        self.cumulative_daily_costs = 0

        self.create_agent_schedules()
        self.create_front_desk(planning_method)
        self.create_departments()
        self.create_home()
        
        self.datacollector.collect(self)

    def get_normally_distributed_timestamps(self, size: int = 1, planned: bool = False) -> List[int]:
        mean, std_dev = self.datamanager.get_mean_std_by_planned(planned)
        min_value = 0
        max_value = 24 * 3600  # 24 hours in seconds

        # Generate a normal random value
        timestamps = np.random.normal(mean, std_dev, size=size)

        # Clamp the value between min and max
        return [max(min(int(timestamp), max_value), min_value) for timestamp in timestamps]

    """
        This function will create all planned agents using the existing self.create_agent function
        It will loop through an entire year (each day) and determine the agents that have to spawn on that day

        This function is used in the init to create a schedule for when an agent should spawn

    """
    def create_agent_schedules(self) -> None:
        self.agent_schedules = {}
        amount = 0
        for i in range(365):
            percentage = self.datamanager.get_amount_percentage_by_day(i + 1, True)
            
            amount_of_agents_today = int(self.amount * percentage)
            amount += percentage
            schedule = np.sort(self.get_normally_distributed_timestamps(amount_of_agents_today, True))
            self.agent_schedules[(i+1)] = schedule

        
        
    def create_agent(self, planned: bool = False) -> None:
        data = self.datamanager.create_patients(1)[0]
        # x = self.random.randint(0, self.space.width - 1)
        # y = self.random.randint(0, self.space.height - 1)
        
        agent = Patient(self, age=data["age"],  gender=data["gender"], planned=planned, spec=data["ref_spec"], los_icu=data["los_icu"])
        pos = self.agents_by_type[Home][0].pos
        self.space.place_agent(agent, pos)    
        
    def create_front_desk(self, planning_method: int) -> None: 
        pos = (int(self.space.width / 2), int(self.space.height / 4))
        agent = Frontdesk(self, pos=pos, planning_method=planning_method)
        self.space.place_agent(agent, pos)

    def create_departments(self) -> None: 
        for i in range(len(self.departments.value)):
            index = i + 1
            pos = (int(self.space.width / (len(self.departments.value) + 1)) * index, int(self.space.height - self.space.height / 4))
            
            agent = Department(self, specs=self.departments.value[i], capacity=int(self.capacity * self.distribution.value[i]), is_specialized=self.is_specialized.value[i])
            self.space.place_agent(agent, pos)

    def create_home(self) -> None:
        agent = Home(self, self.create_agent)
        self.space.place_agent(agent, (0, 0))

    def get_front_desk_location(self) -> tuple[int, int]:
        return self.agents_by_type[Frontdesk][0].row_pos
    
    def get_icu_department(self, spec: str) -> Department:
        result = None
        for department in self.agents_by_type[Department]:
            if spec in department.specs:
                result = department
        return result

    def capture_costs_and_capacity_data(self) -> None:
        # IC costs 2500 euros per day so we divide it by the amount of seconds in a day and multiply it by clock_speed to get costs per second per bed

        cost_per_bed_per_step = 2500 / (60 * 60 * 24) * self.clock.clock_speed        
        cost_per_step = sum([cost_per_bed_per_step * department.current_capacity for department in self.agents_by_type[Department]])

        self.cumulative_daily_costs += cost_per_step
        self.cumulative_hourly_costs += cost_per_step

        if(self.current_hour != self.clock.hour):
            self.datacollector.add_table_row("costs", {
                "date": self.clock.get_time(True),
                "amount_empty_beds":  sum([department.current_capacity for department in self.agents_by_type[Department]]),
                "cumulative_hourly_costs": self.cumulative_hourly_costs,
                "cumulative_daily_costs": self.cumulative_daily_costs
            })

            capacity_data = {
                "date": self.clock.get_time(True)
            }

            for department in self.agents_by_type[Department]:
                key = ", ".join(department.specs)
                capacity_data[key] = department.current_capacity

            self.datacollector.add_table_row("capacity", capacity_data)

            self.current_hour = self.clock.hour
            self.cumulative_hourly_costs = 0

        if(self.current_day != self.clock.day):
            self.current_day = self.clock.day
            self.cumulative_daily_costs = 0
        
        pass

    def step(self) -> None:
        self.clock.step()
        self.agents.do("step")
        self.datacollector.collect(self)
        

        self.capture_costs_and_capacity_data()

        if(self.current_year != self.clock.year):
            self.current_year = self.clock.year
            self.create_agent_schedules()
        
        if(self.clock.day == 25 and self.clock.hour == 23 and self.clock.minute == 50):
            print(self.clock.get_time())
        return super().step()
    
