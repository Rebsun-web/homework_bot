class TokensValueException(Exception):
    """Класс проверки токенов на сущестование."""

    pass


class RequestStatusExeption(Exception):
    """Класс проверки статуса респонса."""

    pass


class NoStatusOrUndocumenated(Exception):
    """Класс проверки статуса респонса."""

    pass


class NoKeyHomeworksInResponse(Exception):
    """Класс проверки наличия ключа в словаре респонса."""

    pass


class HwStatusDidNotChange(Exception):
    """Класс проверки наличия ключа в словаре респонса."""

    pass


class HwHasNotBeenSent(Exception):
    """Класс проверки наличия ключа в словаре респонса."""

    pass
