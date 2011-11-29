import math
from gamera.core import *
from gamera.toolkits import musicstaves

from optparse import OptionParser
import os

import logging
lg = logging.getLogger('StaffFinder')
f = logging.Formatter("%(levelname)s %(asctime)s On Line: %(lineno)d %(message)s")
h = logging.StreamHandler()
h.setFormatter(f)
lg.setLevel(logging.DEBUG)
lg.addHandler(h)

pi = 3.14159265358979

init_gamera()




# stafffinder methods, horizontal approach
def new_candidate_set(candidate_points):
    """ Discards x-points without y-values, creating a new set of candidate points"""
    new_set = []
    num_candidate_points = len(candidate_points)

    for i in range(num_candidate_points):
        if len(candidate_points[i])>1:
            new_set.append(candidate_points[i])
    candidate_points = new_set
    num_candidate_points = len(candidate_points)
    return candidate_points

def max_vector_length(candidate_points):
    """ Checks the maximum vector length"""
    l = 0
    for point in candidate_points:
        if len(point)> l:
            l = len(point)
    return l

def vertical_representation(candidate_points, max_vector_length):
    """Transforms the horizontal to a vertical representation of vectors"""
    horizontal_vectors = []
    for i in range(max_vector_length):
        points = []
        for j in range(len(candidate_points)):
            try:
                points.append(candidate_points[j][i])
            except: 
                pass
        horizontal_vectors.append(points)
    return horizontal_vectors

#  I AM PROCESSING ONE AT A TIME, CHANGE FOR ALL FOR DOING THE POPPING AND INSERTING
def discard_outliers(vector, no_of_points):
    """Returns the outliers points for a specific staffline"""
    idx_to_change = []
    idx_to_keep = []
    for i in range(no_of_points - 1):
        relation = float(vector[i+1]-vector[i])/72 # (delta_y/delta_x, 72 is the default yY difference (change this)
        angle = math.atan(relation)
        # print i, vector[i], angle
        if (pi/12) > angle > (-pi/12): # Maximum allowed slope: 15 degrees 
            idx_to_keep.append(i)

        else:
            idx_to_change.append(i)
            # print "OOPS"
    idx_to_keep.append(no_of_points - 1)
    print "INDEXES TO CHANGE: {0} AND KEEP: {1}".format(idx_to_change, idx_to_keep)
    newvector = vector
    for i in range(len(idx_to_change)):
        newvector.pop(i) # new vector without outliers
    # print "NEWVECTOR: \n{0}".format(newvector)
    a, b, RR = linreg(idx_to_keep, vector)
    # print "A, B: {0}, {1}".format(a, b)
    for i in idx_to_change:
        newvector.insert(i, int(i*a + b))
    print "NEWVECTOR: \n{0}\n".format(newvector)
    return newvector, idx_to_change

def linreg(X, Y):
    """
    Summary
        Linear regression of y = ax + b
    Usage
        real, real, real = linreg(list, list)
    Returns coefficients to the regression line "y=ax+b" from x[] and y[], and R^2 Value
    """
    if len(X) != len(Y):  raise ValueError, 'unequal length'
    N = len(X)
    Sx = Sy = Sxx = Syy = Sxy = 0.0
    for x, y in map(None, X, Y):
        Sx = Sx + x
        Sy = Sy + y
        Sxx = Sxx + x*x
        Syy = Syy + y*y
        Sxy = Sxy + x*y
    det = Sxx * N - Sx * Sx
    a, b = (Sxy * N - Sy * Sx)/det, (Sxx * Sy - Sx * Sxy)/det
    meanerror = residual = 0.0
    for x, y in map(None, X, Y):
        meanerror = meanerror + (y - Sy/N)**2
        residual = residual + (y - a * x - b)**2
    RR = 1 - residual/meanerror
    ss = residual / (N-2)
    Var_a, Var_b = ss * N / det, ss * Sxx / det
    return a, b, RR

def staffvector_retriever(filename):
    """Retrieves and returns the candidate points"""
    image = load_image(filename)
    stafffinder = musicstaves.StaffFinder_gabriel(image)
    candidate_points = stafffinder.find_staves(0, 40, 0.8, -1, 5)
    return candidate_points

def staffspace_height(vector):
    """Calculates the staffspace height, returns the frequency of the maximum
    value, and the value"""
    projection = [0]*5000
    for i, v in enumerate(vector[1:]):
        staffspace_dif = vector[i+1] - vector[i] + 1
        # print i, v, staffspace_dif
        projection.insert(staffspace_dif, projection.pop(staffspace_dif) + 1)
    f_projection_value = max(projection)
    projection_max_value = projection.index(f_projection_value)
    # print '\t', f_projection_value, projection_max_value
    # return f_projection_value, projection_max_value #f_projection_value :frequency of the maximum value
    return projection_max_value 


def despeckle(vector, stfspc):
    """Erases false candidate points by finding if they are too close together"""
    for i, v in enumerate(vector):
        try:
            if vector[i+2]-vector[i+1]<stfspc/2:
                vector.pop(i+1)
                # print "popped \n{0}".format(vector)
        except:
            # print 'error'
            pass
    return vector

def missed_points_writer(vector, stfspc):
    """Searches for and writes missing points according to the staffspace height.
    Returns the properly written vector"""

    no_lines = 4            # 4 for now
    no_staves = 20          # 10 for now
    # if len(vector) < 6:     # if there is less data than a single staff (4 points)
    #     return
    for j in range(no_staves):   
        point_no = no_lines * j
        for i in range(point_no, point_no + no_lines - 1):
            try:
                if vector[i+2] - vector[i+1] > (1.5 * stfspc):  # starting from (i+2) because vector[0] corresponds to x
                    vector.insert(i+2, vector[i+1]+stfspc)
            except:
                # print 'error'
                pass
    # print vector
    return vector

def drawcplistimage(filepath, filename, cplist):
    """Plots crosses in the page according to the candidate points position list"""
    rgb = load_image('/Users/gabriel/Desktop/blank.png') # USING BLANK IMAGE AS CANVAS. CHANGE THIS.
    for cp in cplist:
        for y_point in cp[1:]:
            # lg.debug("X:{0}, Y:{1}".format(cp[0], y_point))
            rgb.draw_marker(FloatPoint(cp[0], y_point), 7, 1, RGBPixel(0, 0, 255))

    print("writing " + filename)
    rgb.save_PNG(filename)
    return rgb

def horizontal_vector(candidate_points, row_no):
    """Creates a horizontal vector with all candidate point values for a certain row"""
    hor_v = []
    for i, v in enumerate(candidate_points):
        if len(v) < 6:   # 4 lines, for now. 
            pass
        else:
            hor_v.append(v[row_no])
    return hor_v
           
def vector_mean(vector):
    """Returns the mean of a vector"""
    nums = [int(x) for x in vector]
    return sum(nums)/len(nums)











if __name__ == "__main__":
    usage = "usage: %prog [options] image_file_path"
    opts = OptionParser(usage = usage)
    options, args = opts.parse_args()
    
    if not args:
        opts.error("You must supply arguments to this script as \nimage_file_path")

    filepath = args[0]
    filename = filepath.split('/')[-1]
    
    candidate_points = staffvector_retriever(filepath)

    global_stfspc = 0         


    # DESPECKLING CLOSER POINTS AND WRITING MISSED POINTS
    #######################
    for i, vector in enumerate(candidate_points):
        stfspc = staffspace_height(vector)
        if stfspc > global_stfspc:   # calculates the biggest, global staff space in a page
            global_stfspc = stfspc
        candidate_points[i] = despeckle(vector, stfspc)
        candidate_points[i] = missed_points_writer(vector, stfspc)

    # lg.debug("\nCANDIDATE POINTS WITH REWRITTEN MISSED POINTS:\n{0}\n".format(candidate_points))

    for v in candidate_points:
        print v

    #  CREATING A VECTOR WITH THE FIRST POINTS ((X,Y) FROM THE TOP OF THE PAGE)
    # USING LINEAR REGRESSION
    #######################
    new_candidate_points = [] # final matrix with corrected points
    x_hor_v = [] # Holds the values for all x-points


    for v in candidate_points:
        if len(v) > 5:
            new_candidate_points.append(v)
    # lg.debug("\nCANDIDATE POINTS WITHOUT SHORT VECTORS:\n{0}\n".format(new_candidate_points))            

    vector_length = len(new_candidate_points)

    for i in range(vector_length):
        for j in range(len(new_candidate_points[i])):
            try:
                print new_candidate_points[j][i],
                dif = new_candidate_points[j+1][i]-new_candidate_points[j][i]
                # print dif, 
                if dif > global_stfspc*0.5:
                    new_candidate_points[j+1][i] = int(0.5*(new_candidate_points[j+2][i] + new_candidate_points[j][i]))
                    print ("{0}C".format(new_candidate_points[j+1][i])), 
            except:
                continue
        print
    






    # for vl in range(len(candidate_points)):
    #     for i in range(5):
    #         try:
    #             print candidate_points[vl][i],
    #         except:
    #             continue



    # print candidate_points
        # nv = []
        # y_hor_v = horizontal_vector(candidate_points, j+1)
        # a, b, RR = linreg(x_hor_v, y_hor_v)

        # lg.debug("\nROW {1}:\n{0}\na:{2}, b:{3}".format(y_hor_v, j, a, b))
        # for i in range(len(y_hor_v) - 1):                               # ALL COLUMNS
        #     dif = y_hor_v[i + 1] - y_hor_v[i]
        #     if dif > global_stfspc:
        #         y_hor_v[i + 1] = int(a*x_hor_v[i]+b)
        #         print 'changed'
        # print y_hor_v




            # lg.debug("\nX:{0}\nY:{1}".format(x_hor_v[i], int(a*x_hor_v[i]+b)))
            # nv.append(int(a*x_hor_v[i]+b))

        # lg.debug("\nnv:\n{0}".format(nv))
        # new_candidate_points.append(nv)
    #     new_candidate_points.append(nv)

    # for i, x in enumerate(x_hor_v):
        # new_candidate_points[i].insert(0,x)


    # lg.debug("\nNEW CANDIDATE POINTS USING LINEAR REGRESSION:\n{0}".format(new_candidate_points))




    # PLOTTING TO A FILE
    ####################
    new_vectors = drawcplistimage(filepath, filename.split('.')[0]+'_LinReg.tif', new_candidate_points)
    # image_rgb = drawcplistimage(filepath, filename, candidate_points)

    print "\nDone!\n"















