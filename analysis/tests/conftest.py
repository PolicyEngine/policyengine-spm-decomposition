"""Shared test fixtures for spm_decomposition tests."""

import numpy as np
import pytest


class MockMicroSeries:
    """Minimal mock of policyengine MicroSeries (weighted pandas-like series)."""

    def __init__(self, values, weights=None):
        self.values = np.asarray(values, dtype=float)
        self._weights = (
            np.asarray(weights, dtype=float)
            if weights is not None
            else np.ones_like(self.values)
        )

    @property
    def weights(self):
        return self._weights

    def sum(self):
        return float(np.sum(self.values * self._weights))

    def mean(self):
        return float(
            np.average(self.values, weights=self._weights)
        )

    def __getitem__(self, mask):
        mask = np.asarray(mask, dtype=bool)
        return MockMicroSeries(self.values[mask], self._weights[mask])

    def __sub__(self, other):
        if isinstance(other, MockMicroSeries):
            return MockMicroSeries(self.values - other.values, self._weights)
        return MockMicroSeries(self.values - other, self._weights)

    def __lt__(self, other):
        if isinstance(other, MockMicroSeries):
            return MockMicroSeries(
                (self.values < other.values).astype(float), self._weights
            )
        return MockMicroSeries((self.values < other).astype(float), self._weights)

    def __eq__(self, other):
        if isinstance(other, MockMicroSeries):
            return MockMicroSeries(
                (self.values == other.values).astype(float), self._weights
            )
        return MockMicroSeries((self.values == other).astype(float), self._weights)


class MockMicrosimulation:
    """Mock Microsimulation that returns pre-set values for calc()."""

    def __init__(self, data: dict[str, MockMicroSeries]):
        self._data = data

    def calc(self, variable: str, period: int = 2024) -> MockMicroSeries:
        if variable not in self._data:
            raise ValueError(f"Variable {variable} not in mock data")
        return self._data[variable]


@pytest.fixture
def mock_sim_factory():
    """Factory fixture that creates MockMicrosimulation instances."""

    def _factory(data: dict[str, MockMicroSeries]) -> MockMicrosimulation:
        return MockMicrosimulation(data)

    return _factory
