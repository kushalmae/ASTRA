"""Template filters for the application."""

def min_filter(*args):
    """Return the minimum value from the arguments.
    This filter can handle both individual values or a list/array.
    """
    if len(args) == 1 and isinstance(args[0], list):
        return min(args[0])
    return min(args)

def max_filter(*args):
    """Return the maximum value from the arguments.
    This filter can handle both individual values or a list/array.
    """
    if len(args) == 1 and isinstance(args[0], list):
        return max(args[0])
    return max(args) 