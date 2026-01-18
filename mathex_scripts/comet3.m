% 3D Spiral Comet
clf
t = 0 : 0.1 : 8*pi;
x = sin(t);
y = cos(t);
z = t;

figure
title('3D Comet Animation')
view(3)
comet3(x, y, z)