import pytest


def test_basic_math():
    """Basic test that always passes"""
    assert 1 + 1 == 2


def test_string_operations():
    """Test string operations"""
    text = "Hello World"
    assert text.lower() == "hello world"
    assert len(text) == 11


@pytest.mark.asyncio
async def test_async_example():
    """Example async test"""
    import asyncio
    await asyncio.sleep(0.001)  # Simulate async operation
    assert True


def test_list_operations():
    """Test list operations"""
    test_list = [1, 2, 3]
    test_list.append(4)
    assert len(test_list) == 4
    assert 4 in test_list