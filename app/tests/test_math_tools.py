from app.math_tools import spacing_to_points, points_from_string_list


def test_spacing_to_pts():
    print(80 * "%", "lin test", 80 * "`", sep='\n')
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


def test_points_from_string_list():
    print(80 * "%", "points_from_string_list test", 80 * "`", sep='\n')
    my_pts = points_from_string_list("1,10,5 ; 10,100,10")
    print(my_pts)
    print(80 * "%", "points_from_string_list test, neg reverse log", 80 * "`", sep='\n')
    my_pts = points_from_string_list("100,10,5 ; 10,100,10", log=True)
    print(my_pts)
    print(80 * "%", "points_from_string_list test, list of pts", 80 * "`", sep='\n')
    my_pts = points_from_string_list(" [ 1,2, 3,4 ,5,] ", log=True)
    print(my_pts)


if __name__ == "__main__":
    test_spacing_to_pts()
    test_points_from_string_list()
