#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  8 11:17:01 2021

@author: mike
"""

from tadasets import torus
from ripser import ripser
from PersistenceLandscapeGrid import PersLandscapeApprox
from visualization import plot_landscape_simple

t = torus()

tph = ripser(t)['dgms']

tpl = PersLandscapeApprox(dgms=tph,hom_deg=1,num_steps=5000)
#%%
plot_landscape_simple(tpl)
