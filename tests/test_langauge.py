from unittest.mock import patch

from not_my_ex.language import Language


def test_language_with_valid_value():
    with patch("not_my_ex.language.input") as mock:
        lang = Language(" PT")
        mock.assert_not_called()
        assert "pt" == lang.name


def test_language_ask_without_value():
    with patch("not_my_ex.language.input") as mock:
        mock.return_value = "pT"
        lang = Language()
        lang.ask()
        mock.assert_called_once()
        assert "pt" == lang.name


def test_language_ask_with_invalid_value():
    with patch("not_my_ex.language.input") as mock:
        mock.side_effect = ("pt-BR", "pt")
        lang = Language()
        lang.ask()
        assert "pt" == lang.name
        assert 2 == mock.call_count
