from math import sqrt
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
    #print "y=ax+b"
    #print "N= %d" % N
    #print "a= %g \\pm t_{%d;\\alpha/2} %g" % (a, N-2, sqrt(Var_a))
    #print "b= %g \\pm t_{%d;\\alpha/2} %g" % (b, N-2, sqrt(Var_b))
    #print "R^2= %g" % RR
    #print "s^2= %g" % ss
    return a, b, RR

if __name__=='__main__':
    #testing
 #    X = [176,
 # 320L,
 # 400L,
 # 481L,
 # 561L,
 # 641L,
 # 721L,
 # 801L,
 # 882L,
 # 962L,
 # 1042L,
 # 1122L,
 # 1202L,
 # 1283L]
 #    Y = [227L,
 # 224L,
 # 196L,
 # 193L,
 # 192L,
 # 190L,
 # 214L,
 # 184L,
 # 182L,
 # 178L,
 # 174L,
 # 174L,
 # 172L,
 # 194L]


    X = [0, 1, 2, 3, 4, 5]
    Y = [0, 1, 2, 3, 4, 5]
    print linreg(X,Y)
    #should be:
    #Slope  Y-Int   R
    #-104.477   378.685 0.702499064