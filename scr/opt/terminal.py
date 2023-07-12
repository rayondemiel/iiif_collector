from ..variables import DEFAULT_CSV


def prompt():
    """
    function ask in the terminal and return value to parse csv.
    """
    information = str(input("Do you want to change parameters by default ? press [Y/N] "))
    if information.lower() == "y":
        return input("In the order [DELEMITER HEADER(int or None) ENCODING] separated by space : ").split()
    elif information.lower() != "n" and information.lower() != "y":
        print("Your reponse isn't correct")
        return prompt()
    else:
        return DEFAULT_CSV[0], DEFAULT_CSV[1], DEFAULT_CSV[2]
