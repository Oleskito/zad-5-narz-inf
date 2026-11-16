from src.manager import Manager
from src.models import Parameters


def test_get_apartment_costs():
    parameters = Parameters()
    manager = Manager(parameters)

    # rachunki wynoszą 910zł
    assert manager.get_apartment_costs("apart-polanka", 2025, 1) == 910.0
    # brak rachunków
    assert manager.get_apartment_costs("apart-polanka", 2025, 2) == 0.0
    # nieistniejące mieszkanie
    assert manager.get_apartment_costs("nieistniejace-mieszkanie", 2025, 1) is None
