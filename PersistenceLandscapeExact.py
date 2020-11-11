"""
Define Persistence Landscape class.
"""
import itertools
import numpy as np
from operator import itemgetter
from auxiliary import union_crit_pairs


class PersistenceLandscapeExact:
    """Persistence Landscape class.

    Parameters
    ----------
    diagrams : list of numpy arrays, optional
        A nested list of numpy arrays, e.g., [array( array([:]), array([:]) ),..., array()]
    Each entry in the list corresponds to a single homological degree.
    Each array represents the birth death pairs for a homology degree.
    Inside each homology degree array are arrays representing birth death pairs.
    Expecting output from ripser: ripser(data_user)['dgms']. Only
    one of diagrams or critical pairs should be specified.

    homological_degree : int
        Represents the homology degree of the persistence diagram.

    critical_pairs: list, optional
        A list of critical pairs (points, values) for specifying a persistence
    landscape. These do not necessarily have to arise from a persistence
    diagram. Only one of diagrams or critical pairs should be specified.


    Methods
    -------
    compute_landscape : stores persistence landscape associated to persistence diagram
        for given homology degree in attribute `critical_paris`

    p_norm: returns p-norm of a landscape
        
    sup_norm: returns sup norm of a landscape
        
    vectorize: returns interpolated y-values of `critical_pairs` on user specified grid

    """
    
    def __init__(
        self, diagrams: list = [], homological_degree: int = 0,
        critical_pairs: list = []):
        if not isinstance(homological_degree, int):
            raise TypeError("homological_degree must be an integer")
        if homological_degree < 0:
            raise ValueError('homological_degree must be positive')
        if not isinstance(diagrams, list):
            raise TypeError("diagrams must be a list")
        ### Do we need to put additional checks here? Make sure its a list of numpy
        ### arrays? etc?
        self.homological_degree = homological_degree
        self.critical_pairs = critical_pairs
        self.diagrams = diagrams
        self.max_depth = len(self.critical_pairs)

    def __repr__(self):
        return (
            "The persistence landscapes of diagrams in homological "
            f"degree {self.homological_degree}"
        )

    def __neg__(self):
        self.compute_landscape()
        return PersistenceLandscapeExact(homological_degree=self.homological_degree,
                                    critical_pairs=[ [[a,-b] for a, b in depth_list]
                                                    for depth_list in self.critical_pairs])
        """
        Computes the negation of a persistence landscape object

        Returns
        -------
        None.
        
        Usage
        -----
        (-P).critical_pairs returns the sum
        """

    def __add__(self, other):
        # This requires a list implementation as written.
        if self.homological_degree != other.homological_degree:
            raise ValueError("homological degrees must match")
        return PersistenceLandscapeExact(
            critical_pairs=union_crit_pairs(self, other),
            homological_degree=self.homological_degree
            )
        """
        Computes the sum of two persistence landscape objects
        
        Parameters
        -------
        other: PersistenceLandscapeExact
            
        Returns
        -------
        None.
        
        Usage
        -----
        (P+Q).critical_pairs returns the sum
        """
    def __sub__(self, other):
        return self + -other
    
        """
        Computes the difference of two persistence landscape objects
        
        Parameters
        -------
        other: PersistenceLandscape
            
        Returns
        -------
        None.
        
        Usage
        -----
        (P-Q).critical_pairs returns the difference
        """

    def __mul__(self, other: float):      
        self.compute_landscape()
        return PersistenceLandscapeExact(
            homological_degree=self.homological_degree,
            critical_pairs=[[(a, other*b) for a, b in depth_list] 
                            for depth_list in self.critical_pairs])
        """
        Computes the product of a persistence landscape object and a float 
        
        Parameters
        -------
        other: float
            the number the persistence landscape will be multiplied by 
            
        Returns
        -------
        None.
        
        Usage
        -----
        (3*P).critical_pairs returns the product
        """
    
    def __rmul__(self,other: float):
        return self.__mul__(other)
        """
        Computes the product of a persistence landscape object and a float 
        
        Parameters
        -------
        other: float
            the number the persistence landscape will be multiplied by 
            
        Returns
        -------
        None.
        
        Usage
        -----
        (P*3).critical_pairs returns the product
    
        """

    def __truediv__(self, other: float):
        return self*(1.0/other)
        """
        Computes the quotient of a persistence landscape object and a float 
        
        Parameters
        -------
        other: float
            the divisor of the persistence landscape object
            
        Returns
        -------
        None.
        
        Usage
        -----
        (P/3).critical_pairs returns the quotient
    
        """

    # Indexing, slicing
    def __getitem__(self, key: slice) -> list:
        """
        Returns a list of critical pairs corresponding in range specified by 
        depth

        Parameters
        ----------
        key : slice object

        Returns
        -------
        list
            The critical pairs of the landscape function corresponding
        to depths given by key
        """
        self.compute_landscape()
        return self.critical_pairs[key]

    def compute_landscape(self, verbose: bool = False) -> list:
        """
        Stores the persistence landscape in `self.critical_pairs` as a list
        
        Parameters
        ----------
        verbose: bool
            if true, progress messages are printed during computation

        """

        verboseprint = print if verbose else lambda *a, **k: None

        # check if landscapes were already computed
        if self.critical_pairs:
            verboseprint('cache was not empty and stored value was returned')
            return self.critical_pairs

        A = self.diagrams[self.homological_degree]    
        # change A into a list
        A = list(A)
        # change inner nparrays into lists
        for i in range(len(A)):
            A[i] = list(A[i])
        # store infitiy values 
        infty_bar = False
        if A[-1][1] == np.inf:
            A. pop(-1)
            infty_bar = True
            # TODO: Do we need this infty_bar variable?
     
        landscape_idx = 0
        L = []

        # Sort A: read from right to left inside ()
        A = sorted(A, key = lambda x: [x[0], -x[1]])
    

        while len(A) != 0:
            verboseprint(f'computing landscape index {landscape_idx+1}...')

            # add a 0 element to begin count of lamda_k
            #size_landscapes = np.append(size_landscapes, [0])

            # pop first term
            b, d = A.pop(0)
            verboseprint(f'(b,d) is ({b},{d})')

            # outer brackets for start of L_k
            L.append([ [-np.inf, 0], [b, 0], [(b+d)/2, (d-b)/2] ] ) 
            
            # check for duplicates of (b,d)
            duplicate = 0
            
            for j, itemj in enumerate(A):
                if itemj == [b,d]:
                    duplicate += 1
                    A.pop(j)
                else:
                    break
           
            while L[landscape_idx][-1] != [np.inf, 0]: 
                
                # if d is > = all remaining pairs, then end lambda
                # includes edge case with (b,d) pairs with the same death time
                if all(d >= _[1] for _ in A):
                    # add to end of L_k
                    L[landscape_idx].extend([ [d,0], [np.inf, 0] ])
                    # for duplicates, add another copy of the last computed lambda
                    for _ in range(duplicate):
                        L.append(L[-1])
                        landscape_idx += 1

                else:
                    # set (b', d')  to be the first term so that d' > d
                    for i, item in enumerate(A):
                        if item[1] > d:
                            b_prime, d_prime = A.pop(i)
                            verboseprint(f'(bp,dp) is ({b_prime},{d_prime})')
                            break


                    # Case I
                    if b_prime > d:
                        L[landscape_idx].extend([ [d, 0] ])


                    # Case II
                    if b_prime >= d:
                        L[landscape_idx].extend([ [b_prime, 0] ])


                    # Case III
                    else:
                        L[landscape_idx].extend([ [(b_prime + d)/2, (d-b_prime)/2] ])
                        # push (b', d) into A in order
                        # find the first b_i in A so that b'<= b_i
                        
                        # push (b', d) to end of list if b' not <= any bi
                        ind = len(A) 
                        for i in range(len(A)):
                            if b_prime <= A[i][0]:
                                ind = i # index to push (b', d) if b' != b_i
                                break
                        # if b' not < = any bi, put at the end of list
                        if ind == len(A):
                            pass
                        # if b' = b_i
                        elif b_prime == A[ind][0]:
                            # pick out (bk,dk) such that b' = bk
                            A_i = [item for item in A if item[0] == b_prime ]
                        
                            # move index to the right one for every d_i such that d < d_i
                            for j in range(len(A_i)):
                                if d < A_i[j][1]:
                                    ind += 1 
                                
                                # d > dk for all k 

                        A.insert(ind ,[b_prime, d])
            
                    L[landscape_idx].extend([ [(b_prime + d_prime)/2, (d_prime-b_prime)/2] ])
                    #size_landscapes[landscape_idx] += 1

                    b,d = b_prime, d_prime # Set (b',d')= (b, d)
                    

            landscape_idx += 1
            
        verboseprint('cache was empty and algorthim was executed')
        # gets rid of infinity terms 
        # As written, this function shouldn't return anything, but rather 
        # update self.critical pairs. 
        self.max_depth = len(L)
        self.critical_pairs = [item[1:-1] for item in L]

    def compute_landscape_by_depth(self, depth: int) -> list:
        """
        Returns the function of depth from `self.critical_pairs` as a list
        
        Parameters
        ----------
        depth: int
            the depth of the desired landscape function
        """
        
        if self.critical_pairs:
            return self.critical_pairs[depth]
        else:
            return self.compute_landscape()[depth]

    def p_norm(self, p: int = 2) -> float:
        """
        Returns the L_{`p`} norm of `self.critical_pairs`
        
        Parameters
        ----------
        p: float, default 2
            value p of the L_{`p`} norm 
        """
        if p == -1:
            return self.infinity_norm()
        if p < -1 or -1 < p < 0:
            raise ValueError(f"p can't be negative, but {p} was passed")
        self.compute_landscape()
        result = 0.
        for l in self.critical_pairs:
            for [[x0,y0], [x1,y1]] in zip(l,l[1:]):
                if y0 == y1:
                    # horizontal line segment
                    result += (np.abs(y0)**p)*(x1-x0)
                    continue
                # slope is well-defined
                slope = (y1 - y0)/(x1-x0)
                b = y0 - slope*x0
                # segment crosses the x-axis
                if (y0 < 0 and y1 > 0) or (y0 > 0 and y1 < 0):
                    z = -b/slope
                    ev_x1 = (slope*x1+b)**(p+1)/(slope*(p+1))
                    ev_x0 = (slope*x0+b)**(p+1)/(slope*(p+1))
                    ev_z = (slope*z++b)**(p+1)/(slope*(p+1))
                    result += np.abs(ev_x1 + ev_x0 -2*ev_z)
                # segment does not cross the x-axis
                else: 
                    ev_x1 = (slope*x1+b)**(p+1)/(slope*(p+1))
                    ev_x0 = (slope*x0+b)**(p+1)/(slope*(p+1))
                    result += np.abs(ev_x1 - ev_x0)
        return (result)**(1.0/p)
                
    def sup_norm(self) -> float:
        """
        Returns the sup norm of `self.critical_pairs`
        """

        self.compute_landscape()
        cvals = list(itertools.chain.from_iterable(self.critical_pairs))
        return max(np.abs(cvals), key=itemgetter(1))[1]
    
    def vectorize(self, start: float = -1., stop: float = -1., num_dims: int = 100) -> list:
        """
        Returns a list of interpolated y-values of `self.critical_pairs` 
        on user specified grid 
        
        Parameters
        ----------
        start: float, default -1
            start value of grid
        if start is not inputed, start is assigned to minimum birth value
        
        stop: float, default -1
            stop value of grid 
        if stop is not inputed, stop is assigned to maximum death value
        
        num_dims: int, default 100
            number of points starting from `start` and ending at `stop`
        
        """
       
        self.compute_landscape()
        # default start and stop value to min/max birth/death value 
        # if start == -1.:
        # if stop == -1.:
        grid = np.linspace(start, stop, num_dims)
        result = []
        # creates sequential pairs of points for each lambda in critical_pairs
        for l in self.critical_pairs:
            xs, ys = zip(*l)
            result.append(np.interp(grid, xs, ys))
        return result
        