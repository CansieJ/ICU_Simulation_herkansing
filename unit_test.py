import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch
from lib.model import ICUModel
from lib.agents import Patient, Frontdesk, Department, Home
from lib.utils import Clock, DataManager
from unittest.mock import MagicMock

class TestICUModel(unittest.TestCase):
    def setUp(self):
        # Initialize a small ICU model for testing
        self.model = ICUModel(seed=1, size=10, amount=100, clock_speed=10)

    def test_patient_initialization(self):
        # Verify if a Patient object is initialized with correct attributes
        patient = Patient(self.model, age=30, gender="M", planned=False, spec="Cardiology", los_icu=2)
        self.assertEqual(patient.age, 30)
        self.assertEqual(patient.gender, "M")
        self.assertEqual(patient.planned, False)
        self.assertEqual(patient.spec, "Cardiology")
        self.assertEqual(patient.los_icu, 2 * 24 * 3600)  # Length of stay in seconds

    def test_patient_movement_and_department_allocation(self):
        # Test if a Patient moves to the correct position and is assigned the correct department
        department = Department(self.model, specs=["Cardiology"], capacity=10)
        self.model.space.place_agent(department, (5, 5))

        patient = Patient(self.model, age=50, gender="M", planned=False, spec="Cardiology", los_icu=1)
        self.model.space.place_agent(patient, (0, 0))
        target_position = (5, 5)
        patient.move(target_position)

        # Verify movement
        self.assertEqual(patient.pos, target_position)

        # Verify department allocation
        patient.set_icu_department(department)
        self.assertEqual(patient.icu_department, department)

    def test_normal_distribution(self):
        # Test if generated timestamps follow a normal distribution and are within valid bounds
        timestamps = self.model.get_normally_distributed_timestamps(size=100)
        mean = np.mean(timestamps)
        std = np.std(timestamps)
        self.assertGreater(mean, 0)
        self.assertLessEqual(max(timestamps), 24 * 3600)

    def test_data_collection(self):
        # Test if the data collector properly tracks admissions and metrics
        self.model.datacollector.collect(self.model)
        admissions_table = self.model.datacollector.get_table_dataframe("admissions")
        self.assertTrue(admissions_table.empty, "Admissions table should be empty initially.")

        capacity = self.model.datacollector.model_vars.get("Capacity", None)
        self.assertIsNotNone(capacity, "Capacity data should be collected.")

    def test_agent_creation_and_environment_setup(self):
        # Test if the correct number of agents is created and placed in the environment
        self.model.agent_schedules[1] = [1, 2, 3, 4]
        self.model.step()
        self.assertEqual(len(self.model.space.agents), 4, "Four patients should be created.")

        # Verify creation of key agents like Departments, Frontdesk, and Home
        self.assertTrue(len(self.model.agents_by_type[Department]) > 0, "Departments should be created.")
        self.assertEqual(len(self.model.agents_by_type[Frontdesk]), 1, "There should be one Frontdesk agent.")
        self.assertEqual(len(self.model.agents_by_type[Home]), 1, "There should be one Home agent.")

class TestDataManager(unittest.TestCase):
    @patch("lib.utils.pd.read_csv")
    def setUp(self, mock_read_csv):
        # Mock CSV read to avoid dependency on an actual file
        mock_read_csv.return_value = pd.DataFrame({
            "adm_icu": ["2025-01-01 08:00:00", "2025-01-01 10:00:00", "2025-01-01 12:00:00"],
            "plan_adm": [1, 1, 0],  # Variation: 1, 1, 0
            "los_icu": [10, 20, 30],
            "ref_spec": ["CARD", "NEU", "CARD"],
            "age": [30, 60, 50],
            "gender": ["M", "F", "M"]
        })
        self.data_manager = DataManager()

    def test_create_patients(self):
        # Verify that patients are correctly created from the mocked data
        patients = self.data_manager.create_patients(size=5)
        self.assertEqual(len(patients), 5)
        self.assertTrue(all("ref_spec" in patient for patient in patients))
        self.assertTrue(all("age" in patient for patient in patients))

class TestClock(unittest.TestCase):
    def setUp(self):
        # Initialize a clock with a speed of 1 second = 1 minute
        self.clock = Clock(clock_speed=1)

    def test_get_day_timestamp(self):
        # Verify day timestamp increments correctly
        self.clock.add_second()
        self.assertEqual(self.clock.get_day_timestamp(), 60)

class TestPatient(unittest.TestCase):
    def setUp(self):
        # Mock the model for testing Patient functionality
        self.mock_model = MagicMock()
        self.mock_model.clock.get_time.return_value = 1
        self.mock_model.clock.get_day_timestamp.return_value = 1000
        self.mock_model.space.move_agent = MagicMock()
        self.mock_model.space.get_cell_list_contents = MagicMock()
        self.mock_model.datacollector.add_table_row = MagicMock()

        # Create a test Patient
        self.patient = Patient(model=self.mock_model, age=30, gender="M", planned=True, spec="CARD", los_icu=1)

    def test_move_patient(self):
        # Test the move method of Patient
        test_location = (5, 5)
        self.patient.move(test_location)

        # Ensure move_agent was called with correct arguments
        self.mock_model.space.move_agent.assert_called_once_with(self.patient, test_location)

class TestFrontdesk(unittest.TestCase):
    def setUp(self):
        # Create a mock model for testing Frontdesk
        self.mock_model = MagicMock()
        self.frontdesk = Frontdesk(model=self.mock_model, pos=(1, 1), planning_method=1)

    def test_deny_patient(self):
        # Verify that denying a patient removes them from the system
        patient_mock = MagicMock()
        self.mock_model.space.get_cell_list_contents.return_value = [patient_mock]

        self.frontdesk.deny_patient(patient_mock)

        # Check that the patient is removed
        self.mock_model.space.remove_agent.assert_called_once_with(patient_mock)

class TestDepartment(unittest.TestCase):
    def setUp(self):
        # Create a mock model for testing Department
        self.mock_model = MagicMock()
        self.department = Department(model=self.mock_model, specs=["CARD"], capacity=2)

    def test_add_patient_to_department(self):
        # Verify that a patient is added to the department correctly
        patient_mock = MagicMock(spec=Patient)
        patient_mock.set_icu_department = MagicMock()

        self.department.patients.append(patient_mock)

        # Ensure the patient is in the department's list
        self.assertIn(patient_mock, self.department.patients)

class TestReschedulePatients(unittest.TestCase):
    def setUp(self):
        # Create a mock model and Frontdesk for rescheduling tests
        self.model = MagicMock()
        self.model.clock.day_index = 1
        self.model.clock.get_day_timestamp.return_value = 86400
        self.model.agent_schedules = {1: np.array([86400, 172800])}
        self.model.get_icu_department.return_value = MagicMock()

        # Create a mock Patient and Frontdesk
        self.patient = MagicMock(spec=Patient)
        self.patient.spec = "CARD"
        self.patient.planned = True
        self.patient.remove = MagicMock()
        self.patient.set_icu_department = MagicMock()
        self.frontdesk = Frontdesk(self.model, pos=(0, 0), planning_method=1)

    def test_reschedule_patient_24(self):
        # Test rescheduling a patient exactly 24 hours later
        index = 2
        if index not in self.model.agent_schedules:
            self.model.agent_schedules[index] = []

        self.frontdesk.reschedule_patient_24(self.patient)
        self.assertTrue(len(self.model.agent_schedules[index]) > 0)

    def test_reschedule_patient_random(self):
        # Test rescheduling a patient to a random day
        random_day = 11
        if random_day not in self.model.agent_schedules:
            self.model.agent_schedules[random_day] = []

        self.frontdesk.reschedule_patient_random(self.patient)
        self.assertTrue(len(self.model.agent_schedules[random_day]) > 0)

    def test_reschedule_patient_lowest(self):
        # Test rescheduling a patient to the day with the least appointments
        self.model.agent_schedules = {1: np.array([86400]), 2: np.array([172800]), 3: np.array([])}
        self.frontdesk.reschedule_patient_lowest(self.patient)

        self.patient.remove.assert_called_once()
        self.assertIn(self.model.clock.get_day_timestamp(), self.model.agent_schedules[3])

if __name__ == '__main__':
    unittest.main()
