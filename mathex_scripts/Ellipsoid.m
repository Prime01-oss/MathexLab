clear; clf;
[x,y,z] = sphere(60);
a=2; b=1; c=0.7;
surf(a*x,b*y,c*z);
axis equal
colormap hot
title('Ellipsoid');
