def dictionary(data: dict) -> dict:
    return data


def iptables(data: dict) -> str:
    def __get_module_str(module: str):
        if module == 'Protocol':
            return "p"
        elif module == 'Source':
            return "s"
        elif module == 'Destination':
            return "d"
        elif module == 'InputInterface':
            return "i"
        elif module == 'OutputInterface':
            return "o"
        else:
            raise ValueError("Error converting module to string")

    __res = list()
    for key in data:
        if key in ['Protocol', 'Source', 'Destination', 'InputInterface', 'OutputInterface', ] and data[key]['items']:
            __res.append(
                f"{'! ' if data[key]['invert'] else ''}-{__get_module_str(key)} " + ",".join(data[key]['items']))
        elif key in ['Accept', 'Drop']:
            __res.append(f"-J {key.upper()}")

    return " ".join(__res)
