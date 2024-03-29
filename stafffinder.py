import math
from gamera.core import *
from gamera.toolkits import musicstaves

from optparse import OptionParser
import os
from PIL import Image

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
    candidate_points = stafffinder.find_staves(0, 20, 0.8, -1, 5)
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
    # rgb = load_image('/Users/gabriel/Desktop/blank.png') # USING BLANK IMAGE AS CANVAS. CHANGE THIS.
    rgb = load_image(filepath)
    rgb = rgb.to_rgb()
    for cp in cplist:
        for y_point in cp[1:]:
            # lg.debug("X:{0}, Y:{1}".format(cp[0], y_point))
            rgb.draw_marker(FloatPoint(cp[0], y_point), 10, 3, RGBPixel(255, 0, 0))

    print("\nwriting " + filename)
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

def pop_insert(matrix, line_no, global_stfpsc, changed_idx):
    """Pops out the minimum difference in x-value of a specific line in a Matrix, and inserts a value 
    based on linear regression whereas is the maximum difference. The differences are calculated
    among the vector's actual values and the fitness function calculated for that vector"""
    x_vector = [] # Holds the values for all x-points
    y_vector = []
    pop_x_vector = []
    pop_y_vector = []
    linreg_y_vector = []


    # FINDING THE INDEXES WITH THE MAXIMUM AND MINIMUM COST
    new_cand_length = len(new_candidate_points)
    # lg.debug("LINE_NO: {1} NCL:{0} MATRIX: {2}".format(new_cand_length, line_no, matrix)) 
    x_vector = [new_candidate_points[i][0] for i in xrange(new_cand_length)]
    # y_vector = [new_candidate_points[i][line_no] for i in xrange(new_cand_length)]
    # lg.debug("\nX_VECTOR:{0}\nY_VECTR{2}:{1}".format(x_vector, y_vector, line_no))


    for i in xrange(new_cand_length):
        try:
            y_vector.append(new_candidate_points[i][line_no])
            lg.debug("y_vector:{0}".format(y_vector))
        except:
            print 'EXCEPTION'
            # y_vector.append(new_candidate_points[i][line_no-1]+global_stfspc)
            y_vector.append(y_vector[-1]+global_stfspc)
            lg.debug("X_VECTOR_LENGTH: {0} Y_VECTOR_LENGTH: {1}".format(x_vector, y_vector))
            continue

    

    a, b, RR = linreg(x_vector, y_vector)
    # lg.debug("RR:{0}".format(RR))
    for i in range(new_cand_length):
        linreg_y_vector.append(int(a*x_vector[i]+b))
    
    # lg.debug("\nCORR Y_VECTOR:{0}".format(corr_y_vector))
    # lg.debug("\nDIFFERENCES:{0}\n".format([y_vector[i]-corr_y_vector[i] for i in range(len(y_vector))]))


    dif = [(y_vector[i]-linreg_y_vector[i]) for i in xrange(len(y_vector))]
    dif_abs = [abs(y_vector[i]-linreg_y_vector[i]) for i in xrange(len(y_vector))]
    max_dif = max(dif_abs)
    idx_max_dif = dif_abs.index(max_dif)
    changed_idx.append(idx_max_dif)

    lg.debug("LINE {3}, DIFFERENCES:{0}, MAX DIF:{1}, IDX:{2}, DIF[IDX_MAX_DIF]:{4}".format(dif, max_dif, idx_max_dif, line_no, dif[idx_max_dif]))
    pop_x_vector = x_vector
    pop_y_vector = y_vector
  
    pop_x_vector.pop(idx_max_dif)
    pop_y_vector.pop(idx_max_dif)
    # lg.debug("popXvector:{0}, popYvector:{1}".format(pop_x_vector, pop_y_vector))

    a1, b1, RR1 = linreg(pop_x_vector, pop_y_vector)
    # lg.debug("a:{0}, b:{1}, line_no:{2}".format(a, b, line_no))
    lg.debug("a1:{0}, b1:{1}, x_vector[line_no]:{2}".format(a1, b1, new_candidate_points[idx_max_dif][0]))
    if dif[idx_max_dif] < -0.25 * global_stfspc:
        lg.debug("CASE 1: POP")
        lg.debug("NCP: {0}, line_no: {1}".format(new_candidate_points[idx_max_dif], line_no))
        new_candidate_points[idx_max_dif].pop(line_no)

        # print 'POP'
    elif dif[idx_max_dif] > 0.25 * global_stfspc:
        lg.debug("CASE 2: INSERT")
        new_candidate_points[idx_max_dif].insert(line_no, int(a1*new_candidate_points[idx_max_dif][0]+b1))
        
        # print 'INSERT'

    return new_candidate_points, changed_idx


def fill_from_first(matrix, staff_no, line_no, global_stfpsc):
    """Fills the non-filled points from the candidate points"""







if __name__ == "__main__":
    usage = "usage: %prog [options] image_file_path"
    opts = OptionParser(usage = usage)
    options, args = opts.parse_args()
    
    if not args:
        opts.error("You must supply arguments to this script as \nimage_file_path")

    filepath = args[0]
    filename = filepath.split('/')[-1]
    
    candidate_points = staffvector_retriever(filepath)
    # lg.debug("\nCANDIDATE POINTS:\n{0}\n".format(candidate_points)) 
    global_stfspc = 0         

    image_rgb = drawcplistimage(filepath, filename.split('.')[0]+'_ORIG.tif', candidate_points)

    # DESPECKLING CLOSER POINTS AND WRITING MISSED POINTS
    #######################
    for i, vector in enumerate(candidate_points):
        stfspc = staffspace_height(vector)
        if stfspc > global_stfspc:   # calculates the biggest, global staff space in a page
            global_stfspc = stfspc
        candidate_points[i] = despeckle(vector, stfspc)
        # candidate_points[i] = missed_points_writer(vector, stfspc)
    # lg.debug("\nCANDIDATE POINTS WITH REWRITTEN MISSED POINTS:\n{0}".format(candidate_points))
    # lg.debug("GLOBAL STAFFSPACE: \t{0}".format(global_stfspc))


    #  CREATING A VECTOR WITH THE FIRST POINTS ((X,Y) FROM THE TOP OF THE PAGE)
    # USING LINEAR REGRESSION
    #######################

    new_candidate_points = [] # final matrix with corrected points


    # CREATING NEW MATRIX WITH VALID CANDIDATE POINTS
    for v in candidate_points:
        if len(v) > 1:
            new_candidate_points.append(v)
    lg.debug("\nNCP:\n{0}".format(new_candidate_points))         


    no_of_staves = 2
    no_of_lines = 4
    for s in xrange(no_of_staves):
        changed_idx = []
        remain_idx = [i for i in xrange(len(new_candidate_points))]
        for l in xrange(no_of_lines):
            if l == 1:
                for i in xrange(10):
                    new_candidate_points, changed_idx = pop_insert(new_candidate_points, (s)*(l), global_stfspc, changed_idx)
                    changed_idx = list(set(changed_idx))
            else:
                pass
        remain_idx = list(set(remain_idx) - set(changed_idx))
        print changed_idx, remain_idx
    
    orig_x_vector = [new_candidate_points[i][0] for i in xrange(len(new_candidate_points))]  
    x_vector = [new_candidate_points[i][0] for i in remain_idx]
    y_vector = [new_candidate_points[i][1] for i in remain_idx]

    print x_vector
    print y_vector
    a, b, RR = linreg(x_vector, y_vector)    


    for i in changed_idx:
        y_vector.insert(i, int(a*orig_x_vector[i]+b))
    print y_vector


    for i in xrange(len(new_candidate_points)):
        new_candidate_points[i][1] = y_vector[i]
0 


    # try:
    #     for line_no in xrange(49):
    #         for i in xrange(40):
    #             new_candidate_points = pop_insert(new_candidate_points, line_no+1, global_stfspc)
    #         lg.debug("LINE: {1}\nNCP:{0}".format(new_candidate_points, line_no))
    # except:
    #     print 'exception in number of lines'



    # PLOTTING TO A FILE
    ####################
    new_vectors = drawcplistimage(filepath, filename.split('.')[0]+'_MEAN.tif', new_candidate_points)
    # img = Image.open(os.path.join(filepath, filename.split('.')[0]+'_MEAN.tif'))
    new_filepath = filepath.split('.')[0]+'_MEAN.tif'

    img = Image.open(new_filepath)
    img.show()
    print "\nDone!\n"















