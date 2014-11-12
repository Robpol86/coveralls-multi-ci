from project.library import sub


def main(condition):
    if condition:
        return sub.sub_func(condition)
    else:
        y = 0
        return sub.sub_func(y)
