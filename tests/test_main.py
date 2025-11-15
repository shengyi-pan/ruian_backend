"""
Author: sy.pan
Date: 2025-08-20 11:06:08
LastEditors: sy.pan
LastEditTime: 2025-11-14 15:18:42
FilePath: /ruian_backend/tests/test_main.py
Description:

Copyright (c) 2025 by sy.pan, All Rights Reserved.
"""

import pytest

from app.main import main, process_data


def test_process_data():
    """
    Just a demo.
    """
    test_data = "test input"
    result = process_data(test_data)
    assert result == test_data
    print("test process success.")


def test_main_function():
    """Test that main function runs without error."""
    # This test just ensures main() doesn't raise an exception
    try:
        main()
        assert True
    except Exception as e:
        pytest.fail(f"main() raised an exception: {e}")


class TestAgentData:
    """Test class for agent data functionality."""

    def test_data_processing(self):
        """Test data processing functionality."""
        sample_data = {"key": "value", "number": 42}
        processed = process_data(sample_data)
        assert processed == sample_data
        print(">>> Success, test_data_processing")

    def test_empty_data(self):
        """Test processing of empty data."""
        empty_data = None
        result = process_data(empty_data)

        assert result is None
        print(">>>Success, test_empty_data")
