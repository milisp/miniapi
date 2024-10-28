import pytest

from miniapi import RequestValidator, ValidationError


class UserValidator(RequestValidator):
    def __init__(self):
        # 定义验证字段
        super().__init__(fields={"username": {"required": True, "type": str, "min_length": 3}})


def test_validator():
    validator = UserValidator()

    # Valid data
    valid_data = {"username": "testuser"}
    assert validator.validate(valid_data) == valid_data

    # Invalid data
    with pytest.raises(ValidationError):
        validator.validate({"username": "ab"})  # 太短

    with pytest.raises(ValidationError):
        validator.validate({"email": "test@example.com"})  # 缺少必需字段
