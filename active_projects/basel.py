#!/usr/bin/env python

from helpers import *

from mobject.tex_mobject import TexMobject
from mobject import Mobject
from mobject.image_mobject import ImageMobject
from mobject.vectorized_mobject import *

from animation.animation import Animation
from animation.transform import *
from animation.simple_animations import *
from animation.continual_animation import *

from animation.playground import *
from topics.geometry import *
from topics.characters import *
from topics.functions import *
from topics.number_line import *
from topics.numerals import *
from topics.combinatorics import *
from scene import Scene
from camera import Camera
from mobject.svg_mobject import *
from mobject.tex_mobject import *


from mobject.vectorized_mobject import *

## To watch one of these scenes, run the following:
## python extract_scene.py -p file_name <SceneName>

inverse_power_law = lambda maxint,scale,cutoff,exponent: \
    (lambda r: maxint * (cutoff/(r/scale+cutoff))**exponent)
inverse_quadratic = lambda maxint,scale,cutoff: inverse_power_law(maxint,scale,cutoff,2)

LIGHT_COLOR = YELLOW
INDICATOR_RADIUS = 0.7
INDICATOR_STROKE_WIDTH = 1
INDICATOR_STROKE_COLOR = WHITE
INDICATOR_TEXT_COLOR = WHITE
INDICATOR_UPDATE_TIME = 0.2
FAST_INDICATOR_UPDATE_TIME = 0.1
OPACITY_FOR_UNIT_INTENSITY = 0.2
SWITCH_ON_RUN_TIME = 2.5
FAST_SWITCH_ON_RUN_TIME = 0.1
NUM_LEVELS = 30
NUM_CONES = 50 # in first lighthouse scene
NUM_VISIBLE_CONES = 5 # ibidem
ARC_TIP_LENGTH = 0.2
AMBIENT_FULL = 1.0
AMBIENT_DIMMED = 0.2

DEGREES = TAU/360

def show_line_length(line):
    v = line.points[1] - line.points[0]
    print v[0]**2 + v[1]**2


class AngleUpdater(ContinualAnimation):
    def __init__(self, angle_arc, lc, **kwargs):
        self.angle_arc = angle_arc
        self.source_point = angle_arc.get_arc_center()
        self.lc = lc
        #self.angle_decimal = angle_decimal
        ContinualAnimation.__init__(self, self.angle_arc, **kwargs)

    def update_mobject(self, dt):
    # angle arc
        new_arc = self.angle_arc.copy().set_bound_angles(
            start = self.lc.start_angle(),
            stop = self.lc.stop_angle()
         )
        new_arc.generate_points()
        new_arc.move_arc_center_to(self.source_point)
        self.angle_arc.points = new_arc.points
        self.angle_arc.add_tip(tip_length = ARC_TIP_LENGTH, at_start = True, at_end = True)



LIGHT_COLOR = YELLOW
DEGREES = 360/TAU
SWITCH_ON_RUN_TIME = 1.5


class AmbientLight(VMobject):

    # Parameters are:
    # * a source point
    # * an opacity function
    # * a light color
    # * a max opacity
    # * a radius (larger than the opacity's dropoff length)
    # * the number of subdivisions (levels, annuli)

    CONFIG = {
        "source_point" : ORIGIN,
        "opacity_function" : lambda r : 1.0/(r+1.0)**2,
        "color" : LIGHT_COLOR,
        "max_opacity" : 1.0,
        "num_levels" : 10,
        "radius" : 5.0
    }

    def generate_points(self):

        # in theory, this method is only called once, right?
        # so removing submobs shd not be necessary
        for submob in self.submobjects:
            self.remove(submob)

        # create annuli
        self.radius = float(self.radius)
        dr = self.radius / self.num_levels
        for r in np.arange(0, self.radius, dr):
            alpha = self.max_opacity * self.opacity_function(r)
            annulus = Annulus(
                inner_radius = r,
                outer_radius = r + dr,
                color = self.color,
                fill_opacity = alpha
            )
            annulus.move_arc_center_to(self.source_point)
            self.add(annulus)



    def move_source_to(self,point):
        self.shift(point - self.source_point)
        self.source_point = np.array(point)
        # for submob in self.submobjects:
        #      if type(submob) == Annulus:
        #         submob.shift(self.source_point - submob.get_center())

    def dimming(self,new_alpha):
        old_alpha = self.max_opacity
        self.max_opacity = new_alpha
        for submob in self.submobjects:
            old_submob_alpha = submob.fill_opacity
            new_submob_alpha = old_submob_alpha * new_alpha/old_alpha
            submob.set_fill(opacity = new_submob_alpha)


class Spotlight(VMobject):

    CONFIG = {
        "source_point" : ORIGIN,
        "opacity_function" : lambda r : 1.0/(r/2+1.0)**2,
        "color" : LIGHT_COLOR,
        "max_opacity" : 1.0,
        "num_levels" : 10,
        "radius" : 5.0,
        "screen" : None,
        "shadow" : VMobject(fill_color = BLACK, stroke_width = 0, fill_opacity = 1.0)
    }

    def track_screen(self):
        self.generate_points()

    def generate_points(self):

        for submob in self.submobjects:
            self.remove(submob)

        if self.screen != None:
            # look for the screen and create annular sectors
            lower_angle, upper_angle = self.viewing_angles(self.screen)
            self.radius = float(self.radius)
            dr = self.radius / self.num_levels
            for r in np.arange(0, self.radius, dr):
                alpha = self.max_opacity * self.opacity_function(r)
                annular_sector = AnnularSector(
                    inner_radius = r,
                    outer_radius = r + dr,
                    color = self.color,
                    fill_opacity = alpha,
                    start_angle = lower_angle,
                    angle = upper_angle - lower_angle
                )
                annular_sector.move_arc_center_to(self.source_point)
                self.add(annular_sector)

        self.update_shadow(point = self.source_point)
        self.add(self.shadow)


    def viewing_angle_of_point(self,point):
        distance_vector = point - self.source_point
        angle = angle_of_vector(distance_vector)
        return angle

    def viewing_angles(self,screen):

        viewing_angles = np.array(map(self.viewing_angle_of_point,
            screen.get_anchors()))
        lower_angle = upper_angle = 0
        if len(viewing_angles) != 0:
            lower_angle = np.min(viewing_angles)
            upper_angle = np.max(viewing_angles)
            
        return lower_angle, upper_angle

    def opening_angle(self):
        l,u = self.viewing_angles(self.screen)
        return u - l

    def start_angle(self):
        l,u = self.viewing_angles(self.screen)
        return l

    def stop_angle(self):
        l,u = self.viewing_angles(self.screen)
        return u

    def move_source_to(self,point):
        print "moving source"
        self.source_point = np.array(point)
        self.recalculate_sectors(point = point, screen = self.screen)
        self.update_shadow(point = point)


    def recalculate_sectors(self, point = ORIGIN, screen = None):
        if screen == None:
            return
        for submob in self.submobject_family():
            if type(submob) == AnnularSector:
                lower_angle, upper_angle = self.viewing_angles(screen)
                new_submob = AnnularSector(
                    start_angle = lower_angle,
                    angle = upper_angle - lower_angle,
                    inner_radius = submob.inner_radius,
                    outer_radius = submob.outer_radius
                )
                new_submob.move_arc_center_to(point)
                submob.points = new_submob.points

    def update_shadow(self,point = ORIGIN):
        use_point = point #self.source_point
        self.shadow.points = self.screen.points
        ray1 = self.screen.points[0] - use_point
        ray2 = self.screen.points[-1] - use_point
        ray1 = ray1/np.linalg.norm(ray1) * 100
        ray1 = rotate_vector(ray1,-TAU/16)
        ray2 = ray2/np.linalg.norm(ray2) * 100
        ray2 = rotate_vector(ray2,TAU/16)
        outpoint1 = self.screen.points[0] + ray1
        outpoint2 = self.screen.points[-1] + ray2
        self.shadow.add_control_points([outpoint2,outpoint1,self.screen.points[0]])
        self.shadow.mark_paths_closed = True


    def dimming(self,new_alpha):
        old_alpha = self.max_opacity
        self.max_opacity = new_alpha
        for submob in self.submobjects:
            if type(submob) != AnnularSector:
                # it's the shadow, don't dim it
                continue
            old_submob_alpha = submob.fill_opacity
            new_submob_alpha = old_submob_alpha * new_alpha/old_alpha
            submob.set_fill(opacity = new_submob_alpha)

    def change_opacity_function(self,new_f):
        self.radius = 120
        self.opacity_function = new_f
        dr = self.radius/self.num_levels

        sectors = []
        for submob in self.submobjects:
            if type(submob) == AnnularSector:
                sectors.append(submob)

        print self.num_levels, len(sectors)
        for (r,submob) in zip(np.arange(0,self.radius,dr),sectors):
            if type(submob) != AnnularSector:
                # it's the shadow, don't dim it
                continue
            alpha = self.opacity_function(r)
            submob.set_fill(opacity = alpha)





class SwitchOn(LaggedStart):
    CONFIG = {
        "lag_ratio": 0.2,
        "run_time": SWITCH_ON_RUN_TIME
    }

    def __init__(self, light, **kwargs):
        if not isinstance(light,AmbientLight) and not isinstance(light,Spotlight):
            raise Exception("Only LightCones and Candles can be switched on")
        LaggedStart.__init__(self,
            FadeIn, light, **kwargs)


class SwitchOff(LaggedStart):
    CONFIG = {
        "lag_ratio": 0.2,
        "run_time": SWITCH_ON_RUN_TIME
    }

    def __init__(self, light, **kwargs):
        if not isinstance(light,AmbientLight) and not isinstance(light,Spotlight):
            raise Exception("Only LightCones and Candles can be switched on")
        light.submobjects = light.submobjects[::-1]
        LaggedStart.__init__(self,
            FadeOut, light, **kwargs)
        light.submobjects = light.submobjects[::-1]





class ScreenTracker(ContinualAnimation):
    def __init__(self, mobject, **kwargs):
        ContinualAnimation.__init__(self, mobject, **kwargs)

    def update_mobject(self, dt):
        self.mobject.recalculate_sectors(
            point = self.mobject.source_point,
            screen = self.mobject.screen)
        self.mobject.update_shadow(self.mobject.source_point)
        


class LightHouse(SVGMobject):
    CONFIG = {
        "file_name" : "lighthouse",
        "height" : 0.5
    }

class LightIndicator(Mobject):
    CONFIG = {
        "radius": 0.5,
        "intensity": 0,
        "opacity_for_unit_intensity": 1
    }

    def generate_points(self):
        self.background = Circle(color=BLACK, radius = self.radius)
        self.background.set_fill(opacity=1)
        self.foreground = Circle(color=self.color, radius = self.radius)
        self.foreground.set_stroke(color=INDICATOR_STROKE_COLOR,width=INDICATOR_STROKE_WIDTH)

        self.add(self.background, self.foreground)
        self.reading = DecimalNumber(self.intensity,num_decimal_points = 3)
        self.reading.set_fill(color=INDICATOR_TEXT_COLOR)
        self.reading.move_to(self.get_center())
        self.add(self.reading)

    def set_intensity(self, new_int):
        self.intensity = new_int
        new_opacity = min(1, new_int * self.opacity_for_unit_intensity)
        self.foreground.set_fill(opacity=new_opacity)
        ChangeDecimalToValue(self.reading, new_int).update(1)
        


class UpdateLightIndicator(AnimationGroup):

    def __init__(self, indicator, intensity, **kwargs):
        if not isinstance(indicator,LightIndicator):
            raise Exception("This transform applies only to LightIndicator")
        
        target_foreground = indicator.copy().set_intensity(intensity).foreground
        change_opacity = Transform(
            indicator.foreground, target_foreground
        )
        changing_decimal = ChangeDecimalToValue(indicator.reading, intensity)
        AnimationGroup.__init__(self, changing_decimal, change_opacity, **kwargs)
        self.mobject = indicator


class IntroScene(PiCreatureScene):

    CONFIG = {
        "rect_height" : 0.2,
        "duration" : 1.0,
        "eq_spacing" : 3 * MED_LARGE_BUFF
    }

    def construct(self):

        randy = self.get_primary_pi_creature()
        randy.scale(0.7).to_corner(DOWN+RIGHT)

        self.force_skipping()

        self.build_up_euler_sum()
        self.build_up_sum_on_number_line()
        self.show_pi_answer()
        self.other_pi_formulas()

        self.revert_to_original_skipping_status()
        

        self.refocus_on_euler_sum()





    def build_up_euler_sum(self):

        self.euler_sum = TexMobject(
           "1", "+", 
           "{1 \\over 4}", "+",
           "{1 \\over 9}", "+",
           "{1 \\over 16}", "+",
           "{1 \\over 25}", "+",
           "\\cdots", "=",
            arg_separator = " \\, "
        )

        self.euler_sum.to_edge(UP)
        self.euler_sum.shift(2*LEFT)
       
        terms = [1./n**2 for n in range(1,6)]
        partial_results_values = np.cumsum(terms)

        self.play(
               FadeIn(self.euler_sum[0], run_time = self.duration)
        )

        equals_sign = self.euler_sum.get_part_by_tex("=")

        self.partial_sum_decimal = DecimalNumber(partial_results_values[1],
                num_decimal_points = 2)
        self.partial_sum_decimal.next_to(equals_sign, RIGHT)



        for i in range(4):

            FadeIn(self.partial_sum_decimal, run_time = self.duration)

            if i == 0:

                self.play(
                    FadeIn(self.euler_sum[1], run_time = self.duration),
                    FadeIn(self.euler_sum[2], run_time = self.duration),
                    FadeIn(equals_sign, run_time = self.duration),
                    FadeIn(self.partial_sum_decimal, run_time = self.duration)
                )

            else:
                self.play(
                    FadeIn(self.euler_sum[2*i+1], run_time = self.duration),
                    FadeIn(self.euler_sum[2*i+2], run_time = self.duration),
                    ChangeDecimalToValue(
                        self.partial_sum_decimal,
                        partial_results_values[i+1], 
                        run_time = self.duration,
                        num_decimal_points = 6,
                        show_ellipsis = True,
                        position_update_func = lambda m: m.next_to(equals_sign, RIGHT)
                    )
                )
                
            self.wait()

        self.q_marks = TextMobject("???").highlight(LIGHT_COLOR)
        self.q_marks.move_to(self.partial_sum_decimal)

        self.play(
            FadeIn(self.euler_sum[-3], run_time = self.duration), # +
            FadeIn(self.euler_sum[-2], run_time = self.duration), # ...
            ReplacementTransform(self.partial_sum_decimal, self.q_marks)
        )



    def build_up_sum_on_number_line(self):

        self.number_line = NumberLine(
            x_min = 0,
            color = WHITE,
            number_at_center = 1,
            stroke_width = 1,
            numbers_with_elongated_ticks = [0,1,2,3],
            numbers_to_show = np.arange(0,5),
            unit_size = 5,
            tick_frequency = 0.2,
            line_to_number_buff = MED_LARGE_BUFF
        )

        self.number_line_labels = self.number_line.get_number_mobjects()
        self.add(self.number_line,self.number_line_labels)
        self.wait()

        # create slabs for series terms

        max_n = 10

        terms = [0] + [1./(n**2) for n in range(1, max_n + 1)]
        series_terms = np.cumsum(terms)
        lines = VGroup()
        self.rects = VGroup()
        slab_colors = [YELLOW, BLUE] * (max_n / 2)

        for t1, t2, color in zip(series_terms, series_terms[1:], slab_colors):
            line = Line(*map(self.number_line.number_to_point, [t1, t2]))
            rect = Rectangle()
            rect.stroke_width = 0
            rect.fill_opacity = 1
            rect.highlight(color)
            rect.stretch_to_fit_height(
                self.rect_height,
            )
            rect.stretch_to_fit_width(line.get_width())
            rect.move_to(line)

            self.rects.add(rect)
            lines.add(line)

        #self.rects.radial_gradient_highlight(ORIGIN, 5, YELLOW, BLUE)
        
        for i in range(5):
            self.play(
                GrowFromPoint(self.rects[i], self.euler_sum[2*i].get_center(),
                    run_time = self.duration)
            )

        for i in range(5, max_n):
            self.play(
                GrowFromPoint(self.rects[i], self.euler_sum[10].get_center(),
                    run_time = self.duration)
            )


    def show_pi_answer(self):

        self.pi_answer = TexMobject("{\\pi^2 \\over 6}").highlight(YELLOW)
        self.pi_answer.move_to(self.partial_sum_decimal)
        self.pi_answer.next_to(self.euler_sum[-1], RIGHT,
            submobject_to_align = self.pi_answer[-2])
        self.play(ReplacementTransform(self.q_marks, self.pi_answer))


    def other_pi_formulas(self):

        self.play(
            FadeOut(self.rects),
            FadeOut(self.number_line_labels),
            FadeOut(self.number_line)
        )

        self.leibniz_sum = TexMobject(
            "1-{1\\over 3}+{1\\over 5}-{1\\over 7}+{1\\over 9}-\\cdots",
            "=", "{\\pi \\over 4}")

        self.wallis_product = TexMobject(
            "{2\\over 1} \\cdot {2\\over 3} \\cdot {4\\over 3} \\cdot {4\\over 5}" +
             "\\cdot {6\\over 5} \\cdot {6\\over 7} \\cdots",
             "=", "{\\pi \\over 2}")

        self.leibniz_sum.next_to(self.euler_sum.get_part_by_tex("="), DOWN,
            buff = self.eq_spacing,
            submobject_to_align = self.leibniz_sum.get_part_by_tex("=")
        )

        self.wallis_product.next_to(self.leibniz_sum.get_part_by_tex("="), DOWN,
            buff = self.eq_spacing,
            submobject_to_align = self.wallis_product.get_part_by_tex("=")
        )


        self.play(
            Write(self.leibniz_sum)
        )
        self.play(
            Write(self.wallis_product)
        )



    def refocus_on_euler_sum(self):

        self.euler_sum.add(self.pi_answer)

        self.play(
            FadeOut(self.leibniz_sum),
            FadeOut(self.wallis_product),
            ApplyMethod(self.euler_sum.shift,
                ORIGIN + 2*UP - self.euler_sum.get_center())
        )

        # focus on pi squared
        pi_squared = self.euler_sum.get_part_by_tex("\\pi")[-3]
        self.play(
            ScaleInPlace(pi_squared,2,rate_func = wiggle)
        )

        q_circle = Circle(color=WHITE,radius=0.8)
        q_mark = TexMobject("?")
        q_mark.next_to(q_circle)

        thought = Group(q_circle, q_mark)
        q_mark.height *= 2
        self.pi_creature_thinks(thought,target_mode = "confused",
            bubble_kwargs = { "height" : 1.5, "width" : 2 })

        self.wait()



class FirstLightHouseScene(PiCreatureScene):

    def construct(self):
        self.remove(self.get_primary_pi_creature())
        self.show_lighthouses_on_number_line()



    def show_lighthouses_on_number_line(self):

        self.number_line = NumberLine(
            x_min = 0,
            color = WHITE,
            number_at_center = 1.6,
            stroke_width = 1,
            numbers_with_elongated_ticks = range(1,5),
            numbers_to_show = range(1,5),
            unit_size = 2,
            tick_frequency = 0.2,
            line_to_number_buff = LARGE_BUFF,
            label_direction = UP,
        )

        self.number_line.label_direction = DOWN

        self.number_line_labels = self.number_line.get_number_mobjects()
        self.add(self.number_line,self.number_line_labels)
        self.wait()

        origin_point = self.number_line.number_to_point(0)

        self.default_pi_creature_class = Randolph
        randy = self.get_primary_pi_creature()

        randy.scale(0.5)
        randy.flip()
        right_pupil = randy.pupils[1]
        randy.next_to(origin_point, LEFT, buff = 0, submobject_to_align = right_pupil)



        light_indicator = LightIndicator(radius = INDICATOR_RADIUS,
            opacity_for_unit_intensity = OPACITY_FOR_UNIT_INTENSITY,
            color = LIGHT_COLOR)
        light_indicator.reading.scale(0.8)

        bubble = ThoughtBubble(direction = RIGHT,
                            width = 2.5, height = 3.5)
        bubble.next_to(randy,LEFT+UP)
        bubble.add_content(light_indicator)

        self.play(
            randy.change, "wave_2",
            ShowCreation(bubble),
            FadeIn(light_indicator)
        )

        lighthouses = []
        lighthouse_pos = []
        ambient_lights = []


        euler_sum_above = TexMobject("1", "+", "{1\over 4}", 
            "+", "{1\over 9}", "+", "{1\over 16}", "+", "{1\over 25}", "+", "{1\over 36}")

        for (i,term) in zip(range(len(euler_sum_above)),euler_sum_above):
            #horizontal alignment with tick marks
            term.next_to(self.number_line.number_to_point(0.5*i+1),UP,buff = 2)
            # vertical alignment with light indicator
            old_y = term.get_center()[1]
            new_y = light_indicator.get_center()[1]
            term.shift([0,new_y - old_y,0])
            


        for i in range(1,NUM_CONES+1):
            lighthouse = LightHouse()
            point = self.number_line.number_to_point(i)
            ambient_light = AmbientLight(
                opacity_function = inverse_quadratic(1,2,1),
                num_levels = NUM_LEVELS,
                radius = 12.0)
            
            ambient_light.move_source_to(point)
            lighthouse.next_to(point,DOWN,0)
            lighthouses.append(lighthouse)
            ambient_lights.append(ambient_light)
            lighthouse_pos.append(point)


        for lh in lighthouses:
            self.add_foreground_mobject(lh)

        light_indicator.set_intensity(0)

        intensities = np.cumsum(np.array([1./n**2 for n in range(1,NUM_CONES+1)]))
        opacities = intensities * light_indicator.opacity_for_unit_intensity

        self.remove_foreground_mobjects(light_indicator)


        # slowly switch on visible light cones and increment indicator
        for (i,ambient_light) in zip(range(NUM_VISIBLE_CONES),ambient_lights[:NUM_VISIBLE_CONES]):
            indicator_start_time = 0.4 * (i+1) * SWITCH_ON_RUN_TIME/ambient_light.radius * self.number_line.unit_size
            indicator_stop_time = indicator_start_time + INDICATOR_UPDATE_TIME
            indicator_rate_func = squish_rate_func(
                smooth,indicator_start_time,indicator_stop_time)
            self.play(
                SwitchOn(ambient_light),
                FadeIn(euler_sum_above[2*i], run_time = SWITCH_ON_RUN_TIME,
                    rate_func = indicator_rate_func),
                FadeIn(euler_sum_above[2*i - 1], run_time = SWITCH_ON_RUN_TIME,
                    rate_func = indicator_rate_func),
                ChangeDecimalToValue(light_indicator.reading,intensities[i],
                    rate_func = indicator_rate_func, run_time = SWITCH_ON_RUN_TIME),
                ApplyMethod(light_indicator.foreground.set_fill,None,opacities[i])
            )

            if i == 0:
                # move a copy out of the thought bubble for comparison
                light_indicator_copy = light_indicator.copy()
                old_y = light_indicator_copy.get_center()[1]
                new_y = self.number_line.get_center()[1]
                self.play(
                    light_indicator_copy.shift,[0, new_y - old_y,0]
                )

        # quickly switch on off-screen light cones and increment indicator
        for (i,ambient_light) in zip(range(NUM_VISIBLE_CONES,NUM_CONES),ambient_lights[NUM_VISIBLE_CONES:NUM_CONES]):
            indicator_start_time = 0.5 * (i+1) * FAST_SWITCH_ON_RUN_TIME/ambient_light.radius * self.number_line.unit_size
            indicator_stop_time = indicator_start_time + FAST_INDICATOR_UPDATE_TIME
            indicator_rate_func = squish_rate_func(#smooth, 0.8, 0.9)
                smooth,indicator_start_time,indicator_stop_time)
            self.play(
                SwitchOn(ambient_light, run_time = FAST_SWITCH_ON_RUN_TIME),
                ChangeDecimalToValue(light_indicator.reading,intensities[i],
                    rate_func = indicator_rate_func, run_time = FAST_SWITCH_ON_RUN_TIME),
                ApplyMethod(light_indicator.foreground.set_fill,None,opacities[i])
            )


        # show limit value in light indicator and an equals sign
        limit_reading = TexMobject("{\pi^2 \over 6}")
        limit_reading.move_to(light_indicator.reading)

        equals_sign = TexMobject("=")
        equals_sign.next_to(randy, UP)
        old_y = equals_sign.get_center()[1]
        new_y = euler_sum_above.get_center()[1]
        equals_sign.shift([0,new_y - old_y,0])

        self.play(
            FadeOut(light_indicator.reading),
            FadeIn(limit_reading),
            FadeIn(equals_sign),
        )

            

        self.wait()

        

class SingleLightHouseScene(PiCreatureScene):

    def construct(self):

        self.create_light_source_and_creature()



    def create_light_source_and_creature(self):

        SCREEN_SIZE = 3.0
        DISTANCE_FROM_LIGHTHOUSE = 10.0
        source_point = [-DISTANCE_FROM_LIGHTHOUSE/2,0,0]
        observer_point = [DISTANCE_FROM_LIGHTHOUSE/2,0,0]

        lighthouse = LightHouse()
        ambient_light = AmbientLight(
            opacity_function = inverse_quadratic(AMBIENT_FULL,2,1),
            num_levels = NUM_LEVELS,
            radius = 10,
            brightness = 1,
        )
        lighthouse.scale(2).next_to(source_point, DOWN, buff = 0)
        ambient_light.move_to(source_point)
        morty = self.get_primary_pi_creature()
        morty.scale(0.5)
        morty.move_to(observer_point)
        self.add(lighthouse)
        self.play(
            SwitchOn(ambient_light)
        )


        screen = Line([0,-1,0],[0,1,0])
        screen.rotate(-TAU/6)
        screen.next_to(morty, LEFT, buff = 1)

        spotlight = Spotlight(
            opacity_function = inverse_quadratic(1,2,1),
            num_levels = NUM_LEVELS,
            radius = 10,
            brightness = 5,
            screen = screen
        )
        spotlight.move_source_to(source_point)


        self.play(
            ApplyMethod(ambient_light.dimming,AMBIENT_DIMMED),
            FadeIn(spotlight))
        self.add(spotlight.shadow)

        self.add_foreground_mobject(morty)

        screen_tracker = ScreenTracker(spotlight)
        # activate ONLY when spotlight is moving!

        self.add(screen_tracker)
        pointing_screen_at_source = ApplyMethod(spotlight.screen.rotate,TAU/6)
        self.play(pointing_screen_at_source)
        



        arc_angle = spotlight.opening_angle()
        # draw arc arrows to show the opening angle
        angle_arc = Arc(radius = 5, start_angle = spotlight.start_angle(),
            angle = spotlight.opening_angle(), tip_length = ARC_TIP_LENGTH)
        #angle_arc.add_tip(at_start = True, at_end = True)
        angle_arc.move_arc_center_to(source_point)
        
        self.add(angle_arc)

        angle_indicator = DecimalNumber(arc_angle/TAU*360,
            num_decimal_points = 0,
            unit = "^\\circ")
        angle_indicator.next_to(angle_arc,RIGHT)
        self.add_foreground_mobject(angle_indicator)

        angle_update_func = lambda x: spotlight.opening_angle()/TAU * 360
        ca3 = ContinualChangingDecimal(angle_indicator,angle_update_func)
        self.add(ca3)

        ca4 = AngleUpdater(angle_arc, spotlight)
        self.add(ca4)

        rotating_screen = ApplyMethod(spotlight.screen.rotate, 
            TAU/8, run_time=1.5)
        #self.wait(2)
        rotating_screen_2 = ApplyMethod(spotlight.screen.rotate, 
            -TAU/4, run_time=3, rate_func = there_and_back)
        #self.wait(2)
        rotating_screen_3 = ApplyMethod(spotlight.screen.rotate, 
            TAU/8, run_time=1.5)

        self.play(rotating_screen)
        self.play(rotating_screen_2)
        self.play(rotating_screen_3)
        

        #self.wait()


### The following is supposed to morph the scene into the Earth scene,
### but it doesn't work


        # # morph into Earth scene

        # globe = Circle(radius = 3)
        # globe.move_to([2,0,0])
        # sun_position = [-100,0,0]
        # #self.add(screen_tracker)
        # print "tuet"
        # self.remove(screen_tracker)
        # new_opacity_function = lambda r: 0.5
        # self.play(
        #     ApplyMethod(lighthouse.move_to,sun_position),
        #     ApplyMethod(ambient_light.move_to,sun_position),
        #     ApplyMethod(spotlight.move_source_to,sun_position),

        # )
        # self.play(
        #     ApplyMethod(spotlight.change_opacity_function,new_opacity_function))

        # self.add(screen_tracker)





class EarthScene(Scene):

    def construct(self):

        DEGREES = TAU/360
        radius = 2.5
        center_x = 3
        theta0 = 80 * DEGREES
        dtheta = 10 * DEGREES
        theta1 = theta0 + dtheta
        screen = Line([center_x - radius * np.cos(theta0),radius * np.sin(theta0),0],
            [center_x - radius * np.cos(theta1),radius * np.sin(theta1),0])
        screen.set_stroke(color = RED, width = 5)

        globe = Circle(radius = radius, stroke_width = 0)
        globe.move_to([center_x,0,0])
        foreground_globe = globe.copy() #  above the shadow
        foreground_globe.radius -= 0.2
        foreground_globe.set_stroke(color = WHITE, width = 1)
        self.add_foreground_mobject(foreground_globe)
        globe.add(screen)

        morty = Mortimer().scale(0.3).next_to(screen, RIGHT, buff = 0.5)
        self.add_foreground_mobject(morty)

        sun = Spotlight(
            opacity_function = lambda r : 0.5,
            num_levels = NUM_LEVELS,
            radius = 100,
            brightness = 5,
            screen = screen
        )

        sun.move_source_to([-90,0,0])
        self.add(globe,sun,screen)

        screen_tracker = ScreenTracker(sun)

        self.add(screen_tracker)
        self.play(
            ApplyMethod(globe.rotate,theta0 + dtheta/2),
            ApplyMethod(morty.move_to,[1.5,0,0])
        )



class ScreenShapingScene(Scene):

    def construct(self):

        DEGREES = TAU / 360

        screen_height = 1.0
        brightness_rect_height = 1.0

        screen = Line([3,-screen_height/2,0],[3,screen_height/2,0], path_arc = 0, num_arc_anchors = 10)

        source = Spotlight(
            opacity_function = inverse_quadratic(1,5,1),
            num_levels = NUM_LEVELS,
            radius = 10,
            brightness = 5,
            screen = screen
        )

        source.move_source_to([-5,0,0])

        lighthouse = LightHouse()
        ambient_light = AmbientLight(
            opacity_function = inverse_quadratic(AMBIENT_DIMMED,1,1),
            num_levels = NUM_LEVELS,
            radius = 10,
            brightness = 1,
        )
        lighthouse.scale(2).next_to(source.source_point,DOWN,buff=0)
        ambient_light.move_source_to(source.source_point)

        self.add(lighthouse, ambient_light,source,screen)

        morty = Mortimer().scale(0.3).next_to(screen, RIGHT, buff = 0.5)
        self.add_foreground_mobject(morty)

        self.wait()

        screen_tracker = ScreenTracker(source)

        self.add(screen_tracker)

        self.play(
            ApplyMethod(screen.set_path_arc, 45 * DEGREES),
        )

        self.play(
            ApplyMethod(screen.set_path_arc, -90 * DEGREES),
        )

        self.play(
            ApplyMethod(screen.set_path_arc, 0),
        )


        # in preparation for the slanting, create a rectangle that show the brightness

        rect_origin = Rectangle(width = 0, height = screen_height).move_to(screen.get_center())
        self.add_foreground_mobject(rect_origin)

        brightness_rect = Rectangle(width = brightness_rect_height,
            height = brightness_rect_height, fill_color = YELLOW, fill_opacity = 0.5)

        brightness_rect.next_to(screen, UP, buff = 1)

        self.play(
            ReplacementTransform(rect_origin,brightness_rect)
        )

        original_screen = screen.copy()
        original_brightness_rect = brightness_rect.copy()
        # for unslanting the screen later

        lower_screen_point, upper_screen_point = screen.get_start_and_end()

        lower_slanted_screen_point = interpolate(
            lower_screen_point, source.source_point, 0.2
        )
        upper_slanted_screen_point = interpolate(
            upper_screen_point, source.source_point, -0.2
        )

        slanted_brightness_rect = brightness_rect.copy()
        slanted_brightness_rect.width *= 2
        slanted_brightness_rect.generate_points()
        slanted_brightness_rect.set_fill(opacity = 0.25)

        slanted_screen = Line(lower_slanted_screen_point,upper_slanted_screen_point,
            path_arc = 0, num_arc_anchors = 10)
        slanted_brightness_rect.move_to(brightness_rect.get_center())

        self.play(
             ReplacementTransform(screen,slanted_screen),
             ReplacementTransform(brightness_rect,slanted_brightness_rect),
        )

        self.wait()

        # Scene 5: constant screen size, changing opening angle
        
        screen = slanted_screen
        source.screen = screen
        self.remove(slanted_screen)

        brightness_rect = slanted_brightness_rect
        self.remove(slanted_brightness_rect)

        
        self.play(
            ReplacementTransform(screen,original_screen),
            ReplacementTransform(brightness_rect,original_brightness_rect),
        )

        self.remove(original_brightness_rect)

        shifted_brightness_rect = brightness_rect.copy()
        shifted_brightness_rect.shift([-3,0,0]).set_fill(opacity = 0.8)

        self.play(
            ApplyMethod(screen.shift,[-3,0,0]),
            ApplyMethod(morty.shift,[-3,0,0]),
            #ApplyMethod(brightness_rect.shift,[-3,0,0]),
            #ApplyMethod(brightness_rect.set_fill,{"opacity": 0.8})
            ReplacementTransform(brightness_rect,shifted_brightness_rect)
        )

        self.remove(original_screen) # was still hiding behind the shadow
        self.remove(shifted_brightness_rect) # also one too many

        # add distance indicator

        left_x = source.source_point[0]
        right_x = screen.get_center()[0]
        indicator_y = -2
        line1 = Arrow([left_x,indicator_y,0],[right_x,indicator_y,0])
        line2 = Arrow([right_x,indicator_y,0],[left_x,indicator_y,0])
        line1.set_fill(color = WHITE)
        line2.set_fill(color = WHITE)
        distance_decimal = Integer(1).next_to(line1,DOWN)
        line = VGroup(line1, line2,distance_decimal)
        self.add(line)


        # move everything away
        distance_to_source = right_x - left_x
        new_right_x = left_x + 2*distance_to_source
        new_line1 = Arrow([left_x,indicator_y,0],[new_right_x,indicator_y,0])
        new_line2 = Arrow([new_right_x,indicator_y,0],[left_x,indicator_y,0])
        new_line1.set_fill(color = WHITE)
        new_line2.set_fill(color = WHITE)
        new_distance_decimal = Integer(2).next_to(new_line1,DOWN)
        new_line = VGroup(new_line1, new_line2,new_distance_decimal)

        new_brightness_rect = brightness_rect.copy()
        new_brightness_rect.shift([distance_to_source,0,0])
        new_brightness_rect.set_fill(opacity = 0.2)

        self.play(
            ReplacementTransform(line,new_line),
            ApplyMethod(screen.shift,[distance_to_source,0,0]),
            Transform(brightness_rect,new_brightness_rect),
            ApplyMethod(morty.shift,[distance_to_source,0,0]),
        )










