class Curve():

    def __init__(self, curve):
        self.cpa = []
        for ct in curve.strip().split(','):
            self.cpa.append(ct.strip().split('|'))

    def evaluate(self, x):
        point_i = 0
        while (point_i < len(self.cpa) - 1):
            if (int(self.cpa[point_i][0]) <= x and int(self.cpa[point_i + 1][0]) > x):
                point_1 = self.cpa[point_i]
                point_2 = self.cpa[point_i + 1]
                delta_x = int(point_2[0]) - int(point_1[0])
                delta_y = int(point_2[1]) - int(point_1[1])
                gradient = float(delta_y)/float(delta_x)
                x_bit = x - int(point_1[0])
                y_bit = int(float(x_bit) * gradient)
                y = int(point_1[1]) + y_bit
                return y

            point_i += 1