clf; clear all;
% 3D Gaussian Surface
x = linspace(-5, 5, 60);
y = linspace(-5, 5, 60);
[X, Y] = meshgrid(x, y);

Z = exp(-(X.^2 + Y.^2)/4);

surf(X, Y, Z);
shading interp
xlabel('X'); ylabel('Y'); zlabel('Z');
title('Gaussian Hill');
