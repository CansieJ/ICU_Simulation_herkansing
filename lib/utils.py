import pandas as pd
import numpy as np
from typing import List, Callable
import os

class Clock:
    def __init__(self, clock_speed: int = 1) -> None:
        self.clock_speed = clock_speed * 60
        self.second = 0
        self.minute = 0
        self.hour = 0
        self.day = 1
        self.month = 1
        self.year = 25

        self.month_mapping = {
            1: 31,
            2: 28,
            3: 31,
            4: 30,
            5: 31,
            6: 30,
            7: 31,
            8: 31,
            9: 30,
            10: 31,
            11: 30,
            12: 31
        }
        self.day_index = 1

        self.year_switch_events: List[Callable] = []
    
    def step(self) -> None:
        self.add_second()

    def add_second(self) -> None:
        self.second += self.clock_speed
        if(self.second >= 60):
            multiplier = int(self.second / 60)
            self.second = 0
            self.add_minute(multiplier)

    def add_minute(self, multiplier) -> None:
        self.minute += multiplier
        if(self.minute >= 60):
            tmp = int(self.minute / 60)
            self.minute = 0
            self.add_hour(multiplier=tmp)

    def add_hour(self, multiplier) -> None:
        self.hour += multiplier
        if(self.hour >= 24):
            tmp = int(self.hour / 24)
            self.hour = 0
            self.add_day(multiplier=tmp)

    def add_day(self, multiplier) -> None:
        self.day_index += 1
        if(self.day_index >= 366):
            self.day_index = 1
        self.day += multiplier
        if (self.day >= self.month_mapping[self.month] + 1):
            tmp = int(self.day / (self.month_mapping[self.month] + 1))
            self.day = 1
            self.add_month(multiplier=tmp)

    def add_month(self, multiplier) -> None:
        self.month += multiplier
        if(self.month >= 13):
            tmp = int(self.month / 12)
            self.month = 1
            self.add_year(multiplier=tmp)

    def add_year(self, multiplier) -> None:
        self.year += multiplier
        if (self.year >= 100):
            self.year = 0
            for event in self.year_switch_events:
                event()

    def get_day_timestamp(self) -> int:
        return self.second + self.minute * 60 + self.hour * 3600

    def get_time(self, full: bool = False) -> None:
        s = "{:02d}".format(self.second)
        m = "{:02d}".format(self.minute)
        h = "{:02d}".format(self.hour)
        d = "{:02d}".format(self.day)
        mo = "{:02d}".format(self.month)
        y = "{:02d}".format(self.year)

        return f"20{y}/{mo}/{d} {h}:{m}:{s}" if full else f"{d}/{mo}/{y} {h}:{m}:{s}" 
    
    @property
    def seconds_in_day (self):
        return 60 * 60 * 24

def get_color (x: float) -> tuple[float, float, float]:
    r = x
    g = 1 - x
    b = 0

    return (r, g, b)


class DataManager:
    def __init__(self) -> None:
        # Dynamisch pad berekenen voor opnames.csv
        opnames_full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "opnames.csv"))

        self.opnames = pd.read_csv(opnames_full_path, delimiter=",")
        self.opnames["date"] = pd.to_datetime(self.opnames["adm_icu"]).dt.day_of_year
        self.opnames["hour"] = pd.to_datetime(self.opnames["adm_icu"]).dt.hour
        self.opnames["year"] = pd.to_datetime(self.opnames["adm_icu"]).dt.year

        self.OPTIONS = {
            "NEC": [12],
            "INT": [2, 4, 7, 41, 47],
            "CARD": [3],
            "CHIR": [9, 10, 11, 13, 39],
            "NEU": [21],
            "CAPU": [29, 50],
            "Other": [15, 18, 19, 20, 23, 36, 48, 98]
        }
        self.opnames = self.opnames.dropna(subset=["los_icu"])
        self.opnames = self.opnames[self.opnames["los_icu"] > 0]
        self.opnames["ref_spec"] = self.opnames["ref_spec"].apply(lambda x: self.get_spec(x))

        # Get two years of covid data 
        covid_data_full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "COVID-19_ic_opnames.csv"))
        self.covid_data = pd.read_csv(covid_data_full_path, delimiter=";")
        self.covid_data["Date_of_statistics"] = pd.to_datetime(self.covid_data["Date_of_statistics"])

        mask = (self.covid_data['Date_of_statistics'] > self.covid_data['Date_of_statistics'][0]) & (self.covid_data['Date_of_statistics'] <= self.covid_data['Date_of_statistics'][730])

        self.covid_data: pd.DataFrame = self.covid_data.loc[mask]

    def get_amount_percentage_by_day(self, day: int = 1, planned: bool = False) -> float:
        opnames = self.opnames[self.opnames["year"] != 2014]

        all_day_of_year_grouped_opnames = opnames.groupby(["year", "date"])
        all_year_totals = all_day_of_year_grouped_opnames.size().groupby(level=0).sum()

        opnames = opnames[opnames["plan_adm"] == (planned)]


        day_of_year_grouped_opnames = opnames.groupby(["year", "date"])

        percentages = day_of_year_grouped_opnames.size() / all_year_totals

        groups = np.sort(list(set([x[0] for x in percentages.keys()])))
        percentages_sum = None
        for group in groups:
            if(type(percentages_sum) == type(None)):
                percentages_sum = percentages.get(group)
            else:
                percentages_sum = percentages_sum.add(percentages.get(group), axis=0, level=0, fill_value=0)
            
            


        percentages_sum = percentages_sum / len(groups)
        
        return percentages_sum[day] if day in percentages_sum else 0
    
    def get_mean_std_by_planned(self, planned: bool = False) -> tuple[float, float]:
        filtered_opnames = self.opnames[self.opnames["plan_adm"] == int(planned)]["hour"]
        return (np.std(filtered_opnames) * 3600, np.mean(filtered_opnames) * 3600)
    
    def get_spec(self, x):
        """Maps a numerical or string ref_spec value to its specialty group."""
        if x in self.OPTIONS.keys():
            return x
        
        parsed_x = int(x)
        for option in self.OPTIONS.keys():
            if parsed_x in self.OPTIONS[option]:
                return option

    def create_patients(self, size: int = 1) -> np.array:
        # opnames_df = pd.read_csv("opnames.csv", delimiter=",")
        # opnames_df["ref_spec"] = opnames_df["ref_spec"].apply(lambda x: self.get_spec(x))
        # opnames_df_dropped = opnames_df.dropna(subset=["los_icu"])

        patients = []
        spec_unique, spec_counts = np.unique(self.opnames["ref_spec"], return_counts=True)
        spec_probabilities = spec_counts / spec_counts.sum()
        patient_specs = np.random.choice(spec_unique, p=spec_probabilities, size=size)
        for spec in patient_specs:
            spec_group = self.opnames[self.opnames["ref_spec"] == spec]

            # Age distribution
            age_unique, age_counts = np.unique(spec_group["age"], return_counts=True)
            age_probabilities = age_counts / age_counts.sum()
            patient_age = np.random.choice(age_unique, p=age_probabilities)

            # Gender distribution
            M_count = len(spec_group[spec_group["gender"] == "M"])
            F_count = len(spec_group[spec_group["gender"] == "F"])
            total_gender = M_count + F_count
            gender_probabilities = [M_count / total_gender, F_count / total_gender]
            patient_gender = np.random.choice(["M", "F"], p=gender_probabilities)

            # ICU length of stay
            los_icu_values = spec_group["los_icu"].values
            patient_los_icu = np.random.choice(los_icu_values)

            patients.append({
                "ref_spec": spec,
                "age": patient_age,
                "gender": patient_gender,
                "los_icu": patient_los_icu
            })

        return np.array(patients)
    
    def get_icu_spike_by_day(self, day: int):
        #https://www.eerstekamer.nl/overig/20230914/interactieve_tijdlijn_ic_3/document#:~:text=Eerst%20worden%20er%20vooral%20regionale,vanaf%2013%20oktober%202020%20noodzakelijk.&text=De%20IC%2Dcapaciteit%20is%20sinds,te%20hoog%20en%20te%20lang.

        if (day > len(self.covid_data)):
            day = day - ((day % len(self.covid_data)) * len(self.covid_data))
        
        admissions = self.covid_data["IC_admission"][day]

        # The amount admissions currently is, is all the IC admissions across the netherlands. To get an estimate of the amount that would have been admitted to AMC we do the following:
        # There were a total of 1150 IC beds, when covid hit this was upscaled to 1350. AMC has around 32 IC beds generally if use the growth and apply it percentage wise
        # to the 32 we should get an estimate of how many beds there were
        amount_of_beds = int(1350 * (32 / 1150))
        percentage_of_admissions = amount_of_beds / 1350
        admissions = int(percentage_of_admissions * admissions)
        
        return admissions if admissions >= 0 else 0
