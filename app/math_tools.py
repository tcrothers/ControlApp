import numpy as np


def points_from_string_list(input_str, sep=";", log=False, curate=True):
    all_pts = []      # function will make a list of numpy arrays
    input_str = input_str.strip()
    if input_str.startswith('[') and input_str.endswith(']'):
        # its a list
        raw_array = np.array([float(val) for val in input_str.strip("[,]").split(',')])
    else:
        substrings = input_str.split(sep)
        for substring in substrings:
            start, stop, num_pts = substring.split(',')
            substr_pts = spacing_to_points(int(start), int(stop), int(num_pts), log_spacing=log)
            all_pts.append(substr_pts)

        raw_array = np.concatenate(all_pts)

    if curate:
        array = order_pts(raw_array)
        array = remove_duplicates(array)
    else:
        array = raw_array
    return array


def remove_duplicates(array_in: np.array, precision=4):
    return np.unique(array_in.round(decimals=precision))


def order_pts(array_in: np.array):
    array_in.sort()
    if array_in[0] > np.median(array_in):
        array_in = array_in[::-1]
    return array_in


def spacing_to_points(first, last, num_pts, log_spacing: bool = False):
    if log_spacing == True:
        lim_difference = np.abs(last - first)
        pts = np.logspace(0, np.log10(lim_difference + 1), num_pts) - 1 + min(first, last)
        if last < first:
            pts = first + last - pts
    else:
        pts = np.linspace(first, last, num_pts)
    return pts


if __name__ == "__main__":
    print(80*"%", "lin test", 80*"`", sep='\n')
    print(spacing_to_points(1, 10, 10))
    print(80 * "%", "reverse lin test", 80 * "`", sep='\n')
    print(spacing_to_points(10, 1, 10))
    print(80 * "%", "negative lin test", 80 * "`", sep='\n')
    print(spacing_to_points(-10, 10, 10))
    print(80 * "%", "negative reverse lin test", 80 * "`", sep='\n')
    print(spacing_to_points(10, -10, 10))
    print(80 * "%", "log test", 80 * "`", sep='\n')
    print(spacing_to_points(1, 10, 10, log_spacing=True))
    print(80 * "%", "reverse log test", 80 * "`", sep='\n')
    print(spacing_to_points(10, 1, 10, log_spacing=True))
    print(80 * "%", "negative log test", 80 * "`", sep='\n')
    print(spacing_to_points(-10, 10, 10, log_spacing=True))
    print(80 * "%", "negative reverse log test", 80 * "`", sep='\n')
    print(spacing_to_points(10, -10, 10, log_spacing=True))

    print(80 * "%", "points_from_string_list test", 80 * "`", sep='\n')
    my_pts = points_from_string_list("1,10,5 ; 10,100,10")
    print(my_pts)
    print(80 * "%", "points_from_string_list test, neg reverse log", 80 * "`", sep='\n')
    my_pts = points_from_string_list("100,10,5 ; 10,100,10", log=True)
    print(my_pts)
