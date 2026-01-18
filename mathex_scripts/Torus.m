clear; clf;
theta = linspace(0,2*pi,60);
phi   = linspace(0,2*pi,60);
[Theta,Phi] = meshgrid(theta,phi);

R = 2;   % big radius
r = 0.7; % tube radius

X = (R + r*cos(Phi)) .* cos(Theta);
Y = (R + r*cos(Phi)) .* sin(Theta);
Z = r*sin(Phi);

surf(X,Y,Z);
axis equal
colormap winter
title('Torus');
