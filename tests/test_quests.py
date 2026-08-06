import pytest
from unittest.mock import patch, MagicMock
from quests import dispatch_quest


@pytest.mark.parametrize("text,expected", [
    ("pull in the pet gacha 10 times", "pull_pet_gacha"),
    ("Pull in the Pet Gacha 10 times", "pull_pet_gacha"),
    ("pull the cookie gacha 10 times", "pull_cookie_gacha"),
    ("pull the character gacha 10 times", "pull_cookie_gacha"),
    ("use 1 chest from your inventory", "use_chest"),
    ("clear stage 3-4", "wait_stage"),
    ("clear stages 10 times", "wait_stage"),
    ("defeat 100 enemies", "wait_enemies"),
    ("bake gear in the oven 3 times", "bake_oven"),
    ("use the furnace 2 times", "bake_oven"),
    ("something totally unknown", "unknown"),
    ("", "unknown"),
])
def test_dispatch_quest(text, expected):
    assert dispatch_quest(text) == expected
