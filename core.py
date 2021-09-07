from enum import Enum


class MODULE_ERROR(Enum):
    NO_ERRORS = 0
    EMPTY_VALUE = 1
    INVALID_VALUE = 2


def is_parent(object_type, parent_type) -> bool:
    if object_type in (parent_type, object,):
        return object_type == parent_type
    else:
        for parent in object_type.__bases__:
            if is_parent(object_type=parent, parent_type=parent_type):
                return True
        return False


class Module(object):

    def __init__(self, *args, invert: bool = False, ) -> None:
        super().__init__()
        self._invert = invert
        self._items = list()
        self._error = MODULE_ERROR.NO_ERRORS
        for __item in args:
            self._error = self.add(__item)

    def _adding(self, value: str):
        self._items.append(value)

    def add(self, value: str) -> MODULE_ERROR:
        self._error = self.check_value(value=value)
        if self._error != MODULE_ERROR.NO_ERRORS:
            return self._error

        self._adding(value=value)
        return MODULE_ERROR.NO_ERRORS

    def check_value(self, value: str) -> MODULE_ERROR:
        return MODULE_ERROR.NO_ERRORS if value.strip() else MODULE_ERROR.EMPTY_VALUE

    def __str__(self) -> str:
        if len(self._items) == 0:
            return str()
        elif len(self._items) == 1:
            return self._items[0]
        else:
            return ",".join(self._items)

    @property
    def value(self) -> str or list:
        __items = list(set(self._items))
        __items.sort()
        if len(__items) == 0:
            return str()
        elif len(__items) == 1:
            return __items[0]
        else:
            return __items

    def export(self, export_method):
        return export_method(data={type(self).__name__: {'invert': self._invert, 'items': self._items, }})

    @property
    def last_error(self) -> MODULE_ERROR:
        return self._error

    @property
    def items(self):
        return self._items

    @property
    def is_inverted(self):
        return self._invert

    @is_inverted.setter
    def is_inverted(self, value: bool):
        self._invert = value


class Action(object):

    def export(self, export_method):
        return export_method(data={type(self).__name__: {}})

    def __str__(self):
        return type(self).__name__

    @property
    def value(self):
        return self.__str__()


class Chain(object):
    pass


class Protocol(Module):

    def check_value(self, value: str = 'tcp') -> MODULE_ERROR:

        def __proto_exists(proto: str) -> bool:
            with open(file='/etc/protocols', mode='r') as f:
                return proto in ([i.split()[0].lower() for i in f.readlines() if
                                      i.strip() and i.lower().find('ipv6') == -1 and i.split()[0] != '#'] + ['any', ])

        self._error = super().check_value(value)
        if self._error == MODULE_ERROR.NO_ERRORS:
            if not __proto_exists(value):
                self._error = MODULE_ERROR.INVALID_VALUE

        return self._error

    def _adding(self, value: str):
        self._items = [value, ]


class HostIpNetwork(Module):

    def check_value(self, value: str) -> MODULE_ERROR:

        def __is_ipv4(ip_address: str) -> bool:
            from ipaddress import IPv4Interface, AddressValueError
            try:
                IPv4Interface(ip_address)
                return True
            except AddressValueError:
                return False

        def __is_hostname(hostname: str) -> bool:
            from socket import gethostbyname, gaierror
            try:
                gethostbyname(hostname)
                return True
            except gaierror:
                return False

        self._error = super().check_value(value)
        if self._error == MODULE_ERROR.NO_ERRORS:
            if not (__is_ipv4(ip_address=value) or __is_hostname(hostname=value)):
                self._error = MODULE_ERROR.INVALID_VALUE

        return self._error


class Source(HostIpNetwork):
    pass


class Destination(HostIpNetwork):
    pass


class Interface(Module):

    def check_value(self, value: str) -> MODULE_ERROR:

        def __iface_exists(iface: str) -> bool:
            with open(file='/proc/net/dev', mode='r') as f:
                if iface[-1] == '+':
                    return bool([True for i in f.readlines()[2:] if i.split()[0].startswith(iface[:-1])])
                else:
                    return iface in [i.split()[0][:-1] for i in f.readlines()[2:]]

        self._error = super().check_value(value)
        if self._error == MODULE_ERROR.NO_ERRORS:
            if not __iface_exists(value):
                self._error = MODULE_ERROR.INVALID_VALUE
        return self._error

    def _adding(self, value: str):
        self._items = [value, ]


class InputInterface(Interface):
    pass


class OutputInterface(Interface):
    pass


class Modules(object):

    def __init__(self) -> None:
        super().__init__()
        self.__items = list()

    def __getitem__(self, key):
        for i in self.__items:
            if type(i) == key:
                return i
        return None

    def __setitem__(self, key, value: str) -> None:
        if is_parent(object_type=key, parent_type=Module):
            __new = self[key]
            if not __new:
                __new = key()
                self.__items.append(__new)
            __new.add(value)
        else:
            raise ValueError(f'Unsupported class <{key}>!')

    @property
    def items(self):
        return self.__items


class Accept(Action):
    pass


class Drop(Action):
    pass


class Return(Action):
    pass


class GoTo(Action):

    def __init__(self, value: Chain, need_return: bool = True):
        super().__init__(self)
        self.__return = need_return
        self.__value = value

    def __set__(self, instance, value: Chain):
        self.__value = value

    def __str__(self):
        return self.value

    def export(self, export_method):
        return export_method(data={type(self).__name__: {'return': self.__return, 'value': self.value}})


class Rule(object):

    def __init__(self) -> None:
        super().__init__()
        self.modules = Modules()
        self.action = Accept()

    def export(self, export_method):
        __export = export_method(dict())
        if type(__export) == dict:
            for __item in self.modules.items:
                __export.update(__item.export(export_method))
            __export.update(self.action.export(export_method))
        elif type(__export) == list:
            __export = [i.export(export_method) for i in self.modules.items]
            __export.append(self.action.export(export_method))
        elif type(__export) == str:
            __export = " ".join([i.export(export_method) for i in self.modules.items if i.value])
            __export += " " + self.action.export(export_method)
        else:
            return None

        return __export.strip()
