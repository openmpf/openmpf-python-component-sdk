import collections
import operator


def get_property(properties, key, default_value, prop_type=None):
    if key not in properties:
        return default_value

    if prop_type is None:
        prop_type = type(default_value)

    value = properties[key]
    if prop_type is bool:
        return value.upper() == 'TRUE'

    try:
        return prop_type(value)
    except (TypeError, ValueError):
        return default_value



Point = collections.namedtuple('Point', ('x', 'y'))


class Size(collections.namedtuple('Size', ('width', 'height'))):
    __slots__ = ()

    @staticmethod
    def from_frame(frame):
        height, width, _ = frame.shape
        return Size(width, height)



def element_wise_op(op, obj1, obj2, target_type=None):
    if target_type is None:
        target_type = type(obj1)
    return target_type(*(op(x, y) for x, y in zip(obj1, obj2)))


class Rect(collections.namedtuple('Rect', ('x', 'y', 'width', 'height'))):
    __slots__ = ()

    @property
    def br(self):
        return Point(self.x + self.width, self.y + self.height)

    @property
    def tl(self):
        return Point(self.x, self.y)

    def empty(self):
        return self.area() <= 0

    def area(self):
        return self.width * self.height

    def size(self):
        return Size(self.width, self.height)

    def union(self, other):
        other = Rect.__rectify(other)

        if self.empty():
            return other
        elif other.empty():
            return self
        else:
            return Rect.from_corners(
                element_wise_op(min, self.tl, other.tl),
                element_wise_op(max, self.br, other.br))


    def intersection(self, other):
        other = Rect.__rectify(other)

        top_left = element_wise_op(max, self.tl, other.tl)
        bottom_right = element_wise_op(min, self.br, other.br)

        if top_left.x >= bottom_right.x or top_left.y >= bottom_right.y:
            return Rect(0, 0, 0, 0)
        return Rect.from_corners(top_left, bottom_right)


    @staticmethod
    def from_corners(point1, point2):
        top_left = element_wise_op(min, point1, point2, Point)
        bottom_right = element_wise_op(max, point1, point2, Point)
        dist = element_wise_op(operator.sub, bottom_right, top_left, Size)
        return Rect.from_corner_and_size(top_left, dist)

    @staticmethod
    def from_corner_and_size(top_left_point, size):
        return Rect(top_left_point[0], top_left_point[1], size[0], size[1])

    @staticmethod
    def from_image_location(image_location):
        return Rect(image_location.x_left_upper, image_location.y_left_upper, image_location.width,
                    image_location.height)

    @staticmethod
    def __rectify(obj):
        if isinstance(obj, Rect):
            return obj
        if len(obj) == 4:
            return Rect(*obj)
        if len(obj) == 2:
            obj1 = obj[0]
            obj2 = obj[1]
            if isinstance(obj2, Point):
                return Rect.from_corners(obj1, obj2)
            if isinstance(obj2, Size):
                return Rect.from_corner_and_size(obj1, obj2)
        raise TypeError('Could not convert argument %s to Rect.' % obj)
