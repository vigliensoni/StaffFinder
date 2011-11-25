import math
from gamera.core import *
from gamera.toolkits import musicstaves


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
    # filename='test1234.png'
    rgb = load_image('/Users/gabriel/Desktop/blank.png')
    for cp in cplist:
        for y_point in cp[1:]:
            rgb.draw_marker(FloatPoint(cp[0], y_point), 7, 1, RGBPixel(0, 0, 255))

    print("writing " + filename + "\n")
    rgb.save_PNG(filename)
    return rgb

def horizontal_vector(candidate_points, row_no):
    """Creates a vector of only first candidate point values"""
    hor_v = []
    for i, v in enumerate(candidate_points):
        if len(v) < 6:   # 4 lines, for now. 
            pass
        else:
            hor_v.append(v[row_no])
            hor_v.reverse() #reverse because y- in the page starts at the top
    return hor_v
           
def vector_mean(vector):
    """Returns the mean of a vector"""
    nums = [int(x) for x in vector]
    return sum(nums)/len(nums)




# MAIN CODE
filepath = '/Volumes/Shared/Gabriel/Salzinnes_Output/StaffOnly/1-001v.tif'
filename = filepath.split('/')[-1]
candidate_points = staffvector_retriever(filepath)

global_stfspc = 0         


for i, vector in enumerate(candidate_points):
    # print vector
    stfspc = staffspace_height(vector)
    if stfspc > global_stfspc:   # calculates the biggest, global staff space in a page
        global_stfspc = stfspc
    candidate_points[i] = despeckle(vector, global_stfspc)
    candidate_points[i] = missed_points_writer(vector, stfspc)

# print candidate_points
x_hor_v = []
for vector in candidate_points:
    if len(vector)>5:   # more than 1 staff
        x_hor_v.append(vector[0])

y_hor_v = horizontal_vector(candidate_points, 1)


print "vector mean: {0} \nx_hor_v {1}\ny_hor_v {2}".format(vector_mean(y_hor_v), x_hor_v, y_hor_v)

a, b, RR = linreg(x_hor_v, y_hor_v)
print a, b

nv = []
for i in range(len(x_hor_v)):
    nv.append([x_hor_v[i], int(a*x_hor_v[i]+b)])

print nv
new_vectors = drawcplistimage(filepath, filename.split('.')[0]+'test.tif', nv)
image_rgb = drawcplistimage(filepath, filename, candidate_points)
print "YIPI"

quit()











### DISCARDING X POINTS WITHOUT Y VALUES, CREATING THE NEW SET OF CANDIDATES
candidate_points = new_candidate_set(candidate_points)
max_vector_length = max_vector_length(candidate_points)
horizontal_vectors = vertical_representation(candidate_points, max_vector_length)

print "OLD VECTOR:\n"
for h in horizontal_vectors:
    print h

for i, h in enumerate(horizontal_vectors[1:]):
    print h, len(h) 
    newvector, idx_to_change = discard_outliers(h, len(h))
    for idx in idx_to_change:
        idx_removed_value = horizontal_vectors[i+1].pop(idx)
        print "IDX VALUE: {0}".format(idx_removed_value)
        horizontal_vectors[i+1].insert(idx, idx_removed_value)

print "NEW VECTOR:\n"
for h in horizontal_vectors:
    print h

# print "NEW CANDIDATE SET:\n{0},\nMAX VECTOR LENGHT:\n{1}".format(candidate_points, max_vector_length)


quit()




### DISCARDING OUTLIERS
points = selected_points
indexes_to_change = []
sum_relation = 0
number_of_points = len(points)
for i in range(number_of_points - 1):
    relation = (float(points[i+1])/float(points[i]))

    if 1.1 > relation > 0.9: # MAGIC NUMBERS, CHECK
        sum_relation = sum_relation + relation
        
    else: 
        number_of_points = number_of_points - 1
        indexes_to_change.append(i)
    print i, points[i], relation

slope = sum_relation / (number_of_points - 1)
new_value = int(points[indexes_to_change[0] + 1]* slope)

print "SLOPE: {0}".format(slope)
print "NEW VALUE: {0}".format(new_value)
print "INDEXES TO CHANGE: {0}".format(indexes_to_change)
candidate_points[indexes_to_change[0]].insert(1, new_value)
print "NEW CANDIDATE POINTS: {0}".format(candidate_points)
































