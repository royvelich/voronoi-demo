import tkinter
from tkinter import Canvas
import itertools
import math
from collections import namedtuple

ArcKey = namedtuple("ArcKey", ["left", "middle", "right"])


def build_arc_key(parabola1, parabola2, parabola3):
    def comp_key(parabola):
        if parabola is None:
            return -float("inf")
        return parabola.site.x

    parabolas = sorted([parabola1, parabola2, parabola3], key=comp_key)
    return ArcKey(parabolas[0], parabolas[1], parabolas[2])


def converges(breakpoint1, breakpoint2):
    dist = math.sqrt(math.pow(breakpoint1.x - breakpoint2.x, 2) + math.pow(breakpoint1.y - breakpoint2.y, 2))
    old_dist = math.sqrt(math.pow(breakpoint1.old_x - breakpoint2.old_x, 2) + math.pow(breakpoint1.old_y - breakpoint2.old_y, 2))
    return dist < old_dist


def get_correct_breakpoint(parabolic_intersection, circle_event):
    left_dist = abs(parabolic_intersection.left_breakpoint.x - circle_event.x)
    right_dist = abs(parabolic_intersection.right_breakpoint.x - circle_event.x)

    if right_dist < left_dist:
        return parabolic_intersection.right_breakpoint

    return parabolic_intersection.left_breakpoint


def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def threewise(iterable):
    a, b, c = itertools.tee(iterable, 3)
    next(b, None)
    next(c, None)
    next(c, None)
    return zip(a, b, c)


class VoronoiDiagramNode:
    def __init__(self, canvas, provider, color="grey", radius=9):
        self.provider = provider
        self.color = color
        self.radius = radius
        self.canvas = canvas
        self.adjacent_edges = []

    @property
    def x(self):
        return self.provider.x

    @property
    def y(self):
        return self.provider.y

    def render(self):
        self.canvas.create_circle(self.x, self.y, self.radius, fill=self.color, outline="", width=0)


class StaticBreakpoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_static = True


class VoronoiDiagramEdge:
    def __init__(self, canvas, node1, node2, color="grey", thickness=3):
        self.color = color
        self.thickness = thickness
        self.node1 = node1
        self.node2 = node2
        self.canvas = canvas

    def render(self):
        self.canvas.create_line(self.node1.x, self.node1.y, self.node2.x, self.node2.y, fill=self.color, width=self.thickness)


class SiteEvent:
    def __init__(self, canvas, x, y, color="red", radius = 9):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color

    def render(self):
        self.canvas.create_circle(self.x, self.y, self.radius, fill=self.color, outline="", width=0)


class CircleEvent:
    def __init__(self, canvas, parabola1, parabola2, parabola3, parabolic_arc, color = "cyan", radius = 9):
        self.canvas = canvas
        self.radius = radius
        self.color = color
        self.parabolas = sorted([parabola1, parabola2, parabola3], key=lambda parabola: parabola.site.x)
        self.left_parabola = self.parabolas[0]
        self.middle_parabola = self.parabolas[1]
        self.right_parabola = self.parabolas[2]
        self.parabolic_arc = parabolic_arc

        x1 = parabola1.site.x
        y1 = parabola1.site.y
        x2 = parabola2.site.x
        y2 = parabola2.site.y
        x3 = parabola3.site.x
        y3 = parabola3.site.y

        a1 = float(x2 - x1) / float(y1 - y2)
        b1 = float(x1*x1 + y1*y1 - (x2*x2 + y2*y2)) / float(2*(y1 - y2))
        a2 = float(x3 - x1) / float(y1 - y3)
        b2 = float(x1*x1 + y1*y1 - (x3*x3 + y3*y3)) / float(2*(y1 - y3))

        self.cx = (b2 - b1) / (a1 - a2)
        self.cy = a1 * self.cx + b1
        self.cr = math.sqrt(math.pow(x1 - self.cx, 2) + math.pow(y1 - self.cy, 2))

        self.bx = self.cx
        self.by = self.cy + self.cr

        self.x = self.bx
        self.y = self.by

    def render(self):
        self.canvas.create_circle(self.x, self.y, self.radius, fill=self.color, width=0)
        self.canvas.create_circle(self.cx, self.cy, self.cr, outline=self.color, width=2)


class SweepLine:
    def __init__(self, canvas, width, max_y, thickness = 3, color = "green"):
        self.y = 0
        self.max_y = max_y
        self.canvas = canvas
        self.width =  width
        self.thickness = thickness
        self.color = color

    def render(self):
        self.canvas.create_line(0, self.y, self.width, self.y, fill=self.color, width=self.thickness)

    def sweep(self, delta):
        updated_y = self.y + delta
        if updated_y >= 0:
            # if updated_y >= 0 and updated_y <= self.max_y:
            self.y = updated_y


class Parabola:
    def __init__(self, canvas, sweep_line, site, color = "red"):
        self.sweep_line = sweep_line
        self.site = site
        self.canvas = canvas
        self.color = color
        self.update()

    def update(self):
        x_s = self.site.x
        y_s = self.site.y
        y_l = self.sweep_line.y
        factor = 1 / float(2 * (y_s - y_l))
        self.a = 1 * factor
        self.b = -2 * x_s * factor
        self.c = float(x_s*x_s + y_s*y_s - y_l*y_l) * factor

    def eval(self, x):
        return self.a * x * x + self.b * x + self.c

    def render(self):
        delta = 900
        x_range = range(self.site.x - delta, self.site.x + delta, 5)
        x = [*x_range]

        for x1, x2 in pairwise(x):
            y1 = self.eval(x1)
            y2 = self.eval(x2)
            self.canvas.create_line(x1, y1, x2, y2, fill=self.color, width=2)


class Breakpoint:
    def __init__(self, canvas, parabolic_intersection, breakpoint_type, radius=7, color="orange"):
        self.canvas = canvas
        self.color = color
        self.radius = radius
        self.parabolic_intersection = parabolic_intersection
        self.breakpoint_type = breakpoint_type
        self._is_static = False
        self.static_x = 0
        self.static_y = 0
        self.node = None

    @property
    def is_static(self):
        return self._is_static

    @is_static.setter
    def is_static(self, value):
        self.static_x = self.x
        self.static_y = self.y
        self._is_static = True

    @property
    def x(self):
        if self._is_static is False:
            if self.breakpoint_type == "left":
                return self.parabolic_intersection.left_x
            elif self.breakpoint_type == "right":
                return self.parabolic_intersection.right_x

        return self.static_x

    @property
    def y(self):
        if self._is_static is False:
            if self.breakpoint_type == "left":
                return self.parabolic_intersection.left_y
            elif self.breakpoint_type == "right":
                return self.parabolic_intersection.right_y

        return self.static_y

    @property
    def old_x(self):
        if self.breakpoint_type == "left":
            return self.parabolic_intersection.old_left_x
        elif self.breakpoint_type == "right":
            return self.parabolic_intersection.old_right_x

    @property
    def old_y(self):
        if self.breakpoint_type == "left":
            return self.parabolic_intersection.old_left_y
        elif self.breakpoint_type == "right":
            return self.parabolic_intersection.old_right_y

    @property
    def left_parabola(self):
        if self.breakpoint_type == "left":
            return self.parabolic_intersection.left_parabola
        elif self.breakpoint_type == "right":
            return self.parabolic_intersection.middle_parabola

    @property
    def right_parabola(self):
        if self.breakpoint_type == "left":
            return self.parabolic_intersection.middle_parabola
        elif self.breakpoint_type == "right":
            return self.parabolic_intersection.right_parabola

    def render(self):
        self.canvas.create_circle(self.x, self.y, self.radius, fill=self.color, width=0)


class ParabolicArc:
    def __init__(self, breakpoint1, breakpoint2, parabola=None):
        self.left_arc = None
        self.right_arc = None
        if breakpoint1 is None and breakpoint2 is not None:
            self.left_breakpoint = None
            self.right_breakpoint = breakpoint2
            self.parabola = self.right_breakpoint.left_parabola
            self.left_parabola = None
            self.right_parabola = self.right_breakpoint.right_parabola
        elif breakpoint1 is not None and breakpoint2 is None:
            self.left_breakpoint = breakpoint1
            self.right_breakpoint = None
            self.parabola = self.left_breakpoint.right_parabola
            self.left_parabola = self.left_breakpoint.left_parabola
            self.right_parabola = None
        elif breakpoint1 is not None and breakpoint2 is not None:
            if breakpoint1.x < breakpoint2.x:
                self.left_breakpoint = breakpoint1
                self.right_breakpoint = breakpoint2
            else:
                self.left_breakpoint = breakpoint2
                self.right_breakpoint = breakpoint1
            self.parabola = self.left_breakpoint.right_parabola
            self.right_parabola = self.right_breakpoint.right_parabola
            self.left_parabola = self.left_breakpoint.left_parabola
        else:
            self.left_breakpoint = None
            self.right_breakpoint = None
            self.right_parabola = None
            self.left_parabola = None
            self.parabola = parabola

    def get_key(self):
        return build_arc_key(self.left_parabola, self.parabola, self.right_parabola)

    def site_below_arc(self, site):
        if self.left_breakpoint is None and self.right_breakpoint is None:
            return True
        if self.left_breakpoint is not None and self.right_breakpoint is None:
            return site.x > self.left_breakpoint.x
        if self.left_breakpoint is None and self.right_breakpoint is not None:
            return site.x <= self.right_breakpoint.x
        else:
            return site.x > self.left_breakpoint.x and site.x <= self.right_breakpoint.x


class ParabolicIntersection:
    def __init__(self, canvas, parabola1, parabola2):
        self.canvas = canvas
        self.parabola1 = parabola1
        self.parabola2 = parabola2
        self.left_breakpoint = Breakpoint(canvas, self, "left")
        self.right_breakpoint = Breakpoint(canvas, self, "right")
        self.left_x = 0
        self.left_y = 0
        self.right_x = 0
        self.right_y = 0
        self.update()

    def update(self):
        a = self.parabola1.a - self.parabola2.a
        b = self.parabola1.b - self.parabola2.b
        c = self.parabola1.c - self.parabola2.c
        m = b*b - 4*a*c
        m_sqrt = math.sqrt(m)
        a_2 = 2*a
        x1 = (-b + m_sqrt) / a_2
        x2 = (-b - m_sqrt) / a_2
        y1 = self.parabola1.eval(x1)
        y2 = self.parabola1.eval(x2)

        self.old_left_x = self.left_x
        self.old_left_y = self.left_y
        self.old_right_x = self.right_x
        self.old_right_y = self.right_y

        if x1 < x2:
            self.left_x = x1
            self.left_y = y1
            self.right_x = x2
            self.right_y = y2
        else:
            self.left_x = x2
            self.left_y = y2
            self.right_x = x1
            self.right_y = y1

        test_x = (self.left_x + self.right_x) / 2
        test_y1 = self.parabola1.eval(test_x)
        test_y2 = self.parabola2.eval(test_x)
        if test_y1 < test_y2:
            self.left_parabola = self.parabola1
            self.middle_parabola = self.parabola2
            self.right_parabola = self.parabola1
        else:
            self.left_parabola = self.parabola2
            self.middle_parabola = self.parabola1
            self.right_parabola = self.parabola2


class VoronoiDiagram(Canvas):
    def init_diagram(self):
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        self.sweep_line = SweepLine(self, canvas_width, canvas_height, 5)
        self.events = [SiteEvent(self, 450, 200, "red"),
                       SiteEvent(self, 1100, 300, "blue"),
                       SiteEvent(self, 900, 600, "white"),
                       SiteEvent(self, 1400, 800, "lightgreen")]
                       # SiteEvent(self, 1400, 100, "magenta")]
                      # Site(self, 200, 500, 5, "yellow")]

        self.sorted_events = sorted(self.events, key=lambda site: site.y, reverse=True)
        self.bind_all("<Key>", self.on_key_pressed)
        self.parabolas = []
        self.parabolic_intersections = []
        self.breakpoints = []
        self.parabolic_arcs = []
        self.circles = []
        self.voronoi_nodes = []
        self.voronoi_edges = []
        self.arc_dict = {}
        self.show_circles = True
        self.show_parabolas = True

    def try_add_circle_event(self, parabolic_arc):
        if parabolic_arc.left_breakpoint is not None and parabolic_arc.right_breakpoint is not None:
            if converges(parabolic_arc.left_breakpoint, parabolic_arc.right_breakpoint):
                circle_event = CircleEvent(self, parabolic_arc.left_parabola, parabolic_arc.parabola, parabolic_arc.right_parabola, parabolic_arc)
                self.circles.append(circle_event)
                self.sorted_events.append(circle_event)
                self.sorted_events.sort(key=lambda site: site.y, reverse=True)

    def on_key_pressed(self, e):
        delta = 2
        key = e.keysym
        if key == "Down":
            self.sweep_line.sweep(delta)

        if key == "Up":
            self.sweep_line.sweep(-delta)

        if key == "c":
            self.show_circles = not self.show_circles

        if key == "p":
            self.show_parabolas = not self.show_parabolas

        for parabola in self.parabolas:
            parabola.update()

        for parabolic_intersection in self.parabolic_intersections:
            parabolic_intersection.update()

        if len(self.sorted_events) > 0:
            current_event = self.sorted_events[-1]
            if current_event.y < self.sweep_line.y:
                self.sorted_events.pop()

                # Site Event
                if isinstance(current_event, SiteEvent):
                    breaching_parabola = Parabola(self, self.sweep_line, current_event, current_event.color)
                    if len(self.parabolas) > 0:
                        for parabolic_arc in self.parabolic_arcs:
                            if parabolic_arc.site_below_arc(current_event):
                                breached_parabola = parabolic_arc.parabola
                                parabolic_intersection = ParabolicIntersection(self, breached_parabola, breaching_parabola)
                                self.parabolic_intersections.append(parabolic_intersection)
                                self.breakpoints.append(parabolic_intersection.left_breakpoint)
                                self.breakpoints.append(parabolic_intersection.right_breakpoint)
                                parabolic_arc1 = ParabolicArc(parabolic_arc.left_breakpoint, parabolic_intersection.left_breakpoint)
                                parabolic_arc2 = ParabolicArc(parabolic_intersection.left_breakpoint, parabolic_intersection.right_breakpoint)
                                parabolic_arc3 = ParabolicArc(parabolic_intersection.right_breakpoint, parabolic_arc.right_breakpoint)
                                self.parabolic_arcs.remove(parabolic_arc)
                                self.parabolic_arcs.append(parabolic_arc1)
                                self.parabolic_arcs.append(parabolic_arc2)
                                self.parabolic_arcs.append(parabolic_arc3)

                                if parabolic_arc.left_arc is not None:
                                    parabolic_arc.left_arc.right_arc = parabolic_arc1

                                if parabolic_arc.right_arc is not None:
                                    parabolic_arc.right_arc.left_arc = parabolic_arc3

                                parabolic_arc1.left_arc = parabolic_arc.left_arc
                                parabolic_arc1.right_arc = parabolic_arc2

                                parabolic_arc2.left_arc = parabolic_arc1
                                parabolic_arc2.right_arc = parabolic_arc3

                                parabolic_arc3.left_arc = parabolic_arc2
                                parabolic_arc3.right_arc = parabolic_arc.right_arc

                                self.try_add_circle_event(parabolic_arc1)
                                self.try_add_circle_event(parabolic_arc2)
                                self.try_add_circle_event(parabolic_arc3)

                                node1 = VoronoiDiagramNode(self, parabolic_intersection.left_breakpoint)
                                node2 = VoronoiDiagramNode(self, parabolic_intersection.right_breakpoint)
                                edge = VoronoiDiagramEdge(self, node1, node2)

                                self.voronoi_nodes.append(node1)
                                self.voronoi_nodes.append(node2)
                                self.voronoi_edges.append(edge)

                                node1.adjacent_edges.append(edge)
                                node2.adjacent_edges.append(edge)

                                parabolic_intersection.left_breakpoint.node = node1
                                parabolic_intersection.right_breakpoint.node = node2
                                break
                    else:
                        parabolic_arc = ParabolicArc(None, None, breaching_parabola)
                        self.parabolic_arcs.append(parabolic_arc)
                        self.arc_dict[parabolic_arc.get_key()] = parabolic_arc

                    self.parabolas.append(breaching_parabola)
                    self.parabolas.sort(key=lambda parabola: parabola.site.x)

                # Circle Event
                elif isinstance(current_event, CircleEvent):
                    parabolic_arc = current_event.parabolic_arc
                    self.parabolic_arcs.remove(parabolic_arc)
                    parabolic_intersection = ParabolicIntersection(self, parabolic_arc.left_parabola, parabolic_arc.right_parabola)
                    self.parabolic_intersections.append(parabolic_intersection)
                    breakpoint = get_correct_breakpoint(parabolic_intersection, current_event)
                    self.breakpoints.append(breakpoint)
                    if parabolic_arc.left_arc is not None:
                        self.breakpoints.remove(parabolic_arc.left_arc.right_breakpoint)
                        parabolic_arc.left_arc.right_breakpoint = breakpoint

                    if parabolic_arc.right_arc is not None:
                        self.breakpoints.remove(parabolic_arc.right_arc.left_breakpoint)
                        parabolic_arc.right_arc.left_breakpoint = breakpoint

                    right_node = parabolic_arc.right_breakpoint.node
                    left_node = parabolic_arc.left_breakpoint.node

                    if right_node is not None and left_node is not None:

                        provider = StaticBreakpoint(breakpoint.x , breakpoint.y)

                        static_node = VoronoiDiagramNode(self, provider)

                        dynamic_node = VoronoiDiagramNode(self, breakpoint)

                        breakpoint.node = dynamic_node

                        for edge in right_node.adjacent_edges:
                            if edge.node1 is right_node:
                                edge.node1 = static_node
                            if edge.node2 is right_node:
                                edge.node2 = static_node

                        for edge in left_node.adjacent_edges:
                            if edge.node1 is left_node:
                                edge.node1 = static_node
                            if edge.node2 is left_node:
                                edge.node2 = static_node

                        new_edge = VoronoiDiagramEdge(self, dynamic_node, static_node)

                        self.voronoi_nodes.append(dynamic_node)
                        self.voronoi_nodes.append(static_node)
                        self.voronoi_nodes.remove(right_node)
                        self.voronoi_nodes.remove(left_node)
                        self.voronoi_edges.append(new_edge)

    def render(self):
        self.sweep_line.render()

        if self.show_parabolas:
            for parabola in self.parabolas:
                parabola.render()

            for breakpoint in self.breakpoints:
                breakpoint.render()

        if self.show_circles:
            for circle in self.circles:
                circle.render()

        for site in self.events:
            site.render()

        for voronoi_edge in self.voronoi_edges:
            voronoi_edge.render()

        for voronoi_node in self.voronoi_nodes:
            if voronoi_node.provider.is_static is True:
                voronoi_node.render()

    def create_circle(self, x, y, r, **kwargs):
        return self.create_oval(x - r, y - r, x + r, y + r, **kwargs)

    def create_circle_arc(self, x, y, r, **kwargs):
        if "start" in kwargs and "end" in kwargs:
            kwargs["extent"] = kwargs["end"] - kwargs["start"]
            del kwargs["end"]
        return self.create_arc(x - r, y - r, x + r, y + r, **kwargs)